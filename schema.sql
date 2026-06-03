-- ============================================================================
-- SQL SCHEMA FOR GAMES MEMBER CLUB (MySQL)
-- Description: Complete schema definition including tables, check constraints,
--              foreign keys, triggers for automated ledger updates, and views.
-- ============================================================================

-- Create database if not exists and use it
CREATE DATABASE IF NOT EXISTS games_member_club;
USE games_member_club;

-- Drop existing views to avoid conflicts
DROP VIEW IF EXISTS view_active_sessions;
DROP VIEW IF EXISTS view_member_financials;
DROP VIEW IF EXISTS view_game_performance;

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS wallet_transactions;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS members;


-- ============================================================================
-- 1. TABLE DEFINITIONS
-- ============================================================================

-- A. members Table
-- Stores club member info, wallet balances, and membership levels.
CREATE TABLE members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    phone VARCHAR(20) UNIQUE NOT NULL,
    wallet_balance DECIMAL(10, 2) DEFAULT 0.00,
    membership_tier VARCHAR(20) DEFAULT 'Bronze',
    join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_age CHECK (age >= 0),
    CONSTRAINT chk_wallet CHECK (wallet_balance >= 0.00),
    CONSTRAINT chk_tier CHECK (membership_tier IN ('Bronze', 'Silver', 'Gold', 'VIP'))
) ENGINE=InnoDB;

-- B. games Table
-- Stores details of individual gaming setups/stations and rates.
CREATE TABLE games (
    game_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    genre VARCHAR(50),
    platform VARCHAR(50) NOT NULL, -- e.g., 'VR', 'PC', 'PS5', 'Xbox', 'Board Game'
    hourly_rate DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Available',
    CONSTRAINT chk_hourly_rate CHECK (hourly_rate >= 0.00),
    CONSTRAINT chk_status CHECK (status IN ('Available', 'Maintenance', 'Occupied'))
) ENGINE=InnoDB;

-- C. bookings Table
-- Tracks gaming sessions. Total cost is automatically calculated upon completion.
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    game_id INT NOT NULL,
    start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME NULL,
    total_cost DECIMAL(10, 2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'Ongoing',
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE RESTRICT,
    CONSTRAINT chk_end_time CHECK (end_time IS NULL OR end_time > start_time),
    CONSTRAINT chk_cost CHECK (total_cost >= 0.00),
    CONSTRAINT chk_booking_status CHECK (status IN ('Ongoing', 'Completed', 'Cancelled'))
) ENGINE=InnoDB;

-- D. wallet_transactions Table
-- Ledger tracking all deposits, payments, and refunds.
CREATE TABLE wallet_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL, -- Positive for credit, negative for debit
    transaction_type VARCHAR(20) NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR(255),
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    CONSTRAINT chk_trans_type CHECK (transaction_type IN ('Deposit', 'Payment', 'Refund'))
) ENGINE=InnoDB;


-- ============================================================================
-- 2. TRIGGERS (BUSINESS LOGIC)
-- ============================================================================

DELIMITER //

-- Trigger 1: prevent_insufficient_funds
-- Before starting a new ongoing booking, ensure the member has enough money
-- to cover at least 1 hour of playing on the chosen game.
CREATE TRIGGER before_booking_insert
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    DECLARE member_bal DECIMAL(10, 2);
    DECLARE game_rate DECIMAL(10, 2);
    
    -- Fetch the member's current balance
    SELECT wallet_balance INTO member_bal FROM members WHERE id = NEW.member_id;
    
    -- Fetch the game's hourly rate
    SELECT hourly_rate INTO game_rate FROM games WHERE game_id = NEW.game_id;
    
    -- Allow booking only if status is not 'Ongoing' or balance >= 1 hour rate
    IF NEW.status = 'Ongoing' AND member_bal < game_rate THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient wallet balance. Members must have at least 1 hour of the game rate to start playing.';
    END IF;
END//


-- Trigger 2: before_booking_update
-- Automatically calculate total_cost based on session duration when booking is completed.
CREATE TRIGGER before_booking_update
BEFORE UPDATE ON bookings
FOR EACH ROW
BEGIN
    DECLARE game_rate DECIMAL(10, 2);
    
    -- Execute calculation only if the booking status transitions to 'Completed'
    IF NEW.status = 'Completed' AND OLD.status = 'Ongoing' THEN
        -- If end_time was not explicitly set, use the current timestamp
        IF NEW.end_time IS NULL THEN
            SET NEW.end_time = CURRENT_TIMESTAMP;
        END IF;
        
        -- Get the hourly rate for the game
        SELECT hourly_rate INTO game_rate FROM games WHERE game_id = NEW.game_id;
        
        -- Calculate total cost: (seconds elapsed / 3600) * hourly_rate, rounded to 2 decimals
        SET NEW.total_cost = ROUND((TIMESTAMPDIFF(SECOND, NEW.start_time, NEW.end_time) / 3600.0) * game_rate, 2);
    END IF;
END//


-- Trigger 3: after_booking_complete
-- Once a booking is completed, generate a payment record in the ledger.
CREATE TRIGGER after_booking_complete
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF NEW.status = 'Completed' AND OLD.status = 'Ongoing' THEN
        -- Log a negative transaction representing the session payment.
        -- This trigger cascades into `after_transaction_insert` to update the member's balance and tier.
        INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
        VALUES (
            NEW.member_id, 
            -NEW.total_cost, 
            'Payment', 
            CONCAT('Session payment for Booking ID ', NEW.booking_id, ' (Game: ', NEW.game_id, ')')
        );
    END IF;
END//


-- Trigger 4: after_transaction_insert
-- Coordinates wallet balance updates and loyalty tier calculations.
CREATE TRIGGER after_transaction_insert
AFTER INSERT ON wallet_transactions
FOR EACH ROW
BEGIN
    DECLARE total_deposited DECIMAL(10, 2);
    
    -- 1. Apply transaction amount directly to user's wallet
    UPDATE members
    SET wallet_balance = wallet_balance + NEW.amount
    WHERE id = NEW.member_id;
    
    -- 2. Calculate lifetime deposits to determine loyalty tiers
    SELECT COALESCE(SUM(amount), 0) INTO total_deposited
    FROM wallet_transactions
    WHERE member_id = NEW.member_id AND transaction_type = 'Deposit';
    
    -- 3. Apply tier upgrades based on lifetime deposits
    IF total_deposited >= 500.00 THEN
        UPDATE members SET membership_tier = 'VIP' WHERE id = NEW.member_id;
    ELSEIF total_deposited >= 200.00 THEN
        UPDATE members SET membership_tier = 'Gold' WHERE id = NEW.member_id;
    ELSEIF total_deposited >= 50.00 THEN
        UPDATE members SET membership_tier = 'Silver' WHERE id = NEW.member_id;
    ELSE
        UPDATE members SET membership_tier = 'Bronze' WHERE id = NEW.member_id;
    END IF;
END//

DELIMITER ;


-- ============================================================================
-- 3. ANALYTICAL VIEWS
-- ============================================================================

-- View A: view_active_sessions
-- Displays members currently playing, their active gaming setup, and start time.
CREATE VIEW view_active_sessions AS
SELECT 
    b.booking_id,
    m.id AS member_id,
    m.name AS member_name,
    g.game_id,
    g.title AS game_title,
    g.platform,
    b.start_time
FROM bookings b
JOIN members m ON b.member_id = m.id
JOIN games g ON b.game_id = g.game_id
WHERE b.status = 'Ongoing';


-- View B: view_member_financials
-- Provides a clean ledger of each member's total top-ups, total spending, and current balance.
CREATE VIEW view_member_financials AS
SELECT 
    m.id AS member_id,
    m.name AS member_name,
    m.membership_tier,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'Deposit' THEN t.amount ELSE 0 END), 0.00) AS total_deposited,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'Payment' THEN ABS(t.amount) ELSE 0 END), 0.00) AS total_spent,
    m.wallet_balance AS current_balance
FROM members m
LEFT JOIN wallet_transactions t ON m.id = t.member_id
GROUP BY m.id, m.name, m.membership_tier, m.wallet_balance;


-- View C: view_game_performance
-- Analyzes usage and revenue of each game.
CREATE VIEW view_game_performance AS
SELECT 
    g.game_id,
    g.title AS game_title,
    g.platform,
    COUNT(b.booking_id) AS total_bookings,
    ROUND(COALESCE(SUM(TIMESTAMPDIFF(SECOND, b.start_time, b.end_time) / 3600.0), 0), 1) AS total_hours_played,
    COALESCE(SUM(b.total_cost), 0.00) AS total_revenue
FROM games g
LEFT JOIN bookings b ON g.game_id = b.game_id AND b.status = 'Completed'
GROUP BY g.game_id, g.title, g.platform;
