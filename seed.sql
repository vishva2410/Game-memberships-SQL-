-- ============================================================================
-- SEED DATA FOR GAMES MEMBER CLUB
-- Description: Inserts initial games, members, and processes deposits to trigger
--              membership tiers (Bronze, Silver, Gold, VIP) and adds some completed
--              and ongoing bookings.
-- ============================================================================

USE games_member_club;

-- Clear any existing records to avoid duplicate keys during re-runs
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE wallet_transactions;
TRUNCATE TABLE bookings;
TRUNCATE TABLE games;
TRUNCATE TABLE members;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Insert Initial Games (Stations)
-- Platforms: 'VR', 'PC', 'PS5', 'Xbox', 'Board Game'
-- Status: 'Available', 'Maintenance', 'Occupied'
INSERT INTO games (title, genre, platform, hourly_rate, status) VALUES
('VR Station Alpha', 'Sci-Fi Shooter / Beat Saber', 'VR', 15.00, 'Available'),
('VR Station Beta', 'Racing Simulator', 'VR', 18.00, 'Available'),
('PC Station 1', 'First-Person Shooter', 'PC', 10.00, 'Available'),
('PC Station 2', 'RPG / MMORPG', 'PC', 10.00, 'Occupied'),
('PC Station 3', 'Strategy', 'PC', 10.00, 'Available'),
('PS5 Station 1', 'Sports / Fighting', 'PS5', 8.00, 'Available'),
('PS5 Station 2', 'Action Adventure', 'PS5', 8.00, 'Available'),
('Xbox Station 1', 'Racing / Platformer', 'Xbox', 8.00, 'Maintenance'),
('Catan Board Game Table', 'Board Games', 'Board Game', 3.00, 'Available'),
('D&D Campaign Lounge', 'TTRPG', 'Board Game', 5.00, 'Available');

-- 2. Insert Initial Members (Initially with 0 wallet balance and Bronze tier)
INSERT INTO members (name, age, phone, wallet_balance, membership_tier, join_date) VALUES
('Alice Smith', 24, '123-456-7890', 0.00, 'Bronze', DATE_SUB(NOW(), INTERVAL 30 DAY)),
('Bob Johnson', 19, '234-567-8901', 0.00, 'Bronze', DATE_SUB(NOW(), INTERVAL 20 DAY)),
('Charlie Brown', 32, '345-678-9012', 0.00, 'Bronze', DATE_SUB(NOW(), INTERVAL 15 DAY)),
('Diana Prince', 28, '456-789-0123', 0.00, 'Bronze', DATE_SUB(NOW(), INTERVAL 10 DAY)),
('Evan Wright', 15, '567-890-1234', 0.00, 'Bronze', DATE_SUB(NOW(), INTERVAL 5 DAY));

-- 3. Perform Initial Wallet Deposits
-- Note: These inserts will trigger `after_transaction_insert` which automatically
-- adjusts the wallet balance AND upgrades the member's loyalty tier!
-- Bronze < $50, Silver >= $50, Gold >= $200, VIP >= $500.

-- Alice deposits $20 (Remains Bronze)
INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
VALUES (1, 20.00, 'Deposit', 'Initial cash top-up');

-- Bob deposits $150 (Upgraded to Silver)
INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
VALUES (2, 150.00, 'Deposit', 'Mobile wallet deposit');

-- Charlie deposits $600 (Upgraded to VIP)
INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
VALUES (3, 600.00, 'Deposit', 'Premium club membership load');

-- Diana deposits $50 (Upgraded to Silver)
INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
VALUES (4, 50.00, 'Deposit', 'Credit card auto-topup');

-- Evan deposits $250 (Upgraded to Gold)
INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
VALUES (5, 250.00, 'Deposit', 'Birthday gift card deposit');


-- 4. Insert Historic (Completed) Bookings
-- Note: Completed bookings require an entry in `bookings` and a matching payment
-- in `wallet_transactions` which deducts the balance.

-- Bob played PS5 Station 1 for 2 hours (Cost: 2 * 8.00 = $16.00)
-- Insert a completed booking
INSERT INTO bookings (booking_id, member_id, game_id, start_time, end_time, total_cost, status)
VALUES (101, 2, 6, DATE_SUB(NOW(), INTERVAL 5 HOUR), DATE_SUB(NOW(), INTERVAL 3 HOUR), 16.00, 'Completed');

-- Corresponding Payment transaction (since triggers run on update, we write the payment directly for seeded completed bookings)
INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
VALUES (2, -16.00, 'Payment', 'Session payment for Booking ID 101 (Game: 6)');


-- Charlie played VR Station Alpha for 3 hours (Cost: 3 * 15.00 = $45.00)
INSERT INTO bookings (booking_id, member_id, game_id, start_time, end_time, total_cost, status)
VALUES (102, 3, 1, DATE_SUB(NOW(), INTERVAL 48 HOUR), DATE_SUB(NOW(), INTERVAL 45 HOUR), 45.00, 'Completed');

-- Corresponding Payment transaction
INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
VALUES (3, -45.00, 'Payment', 'Session payment for Booking ID 102 (Game: 1)');


-- 5. Insert Ongoing Bookings
-- Evan starts playing on PC Station 2 (Ongoing booking)
-- Since Evan's balance ($250) is greater than the hourly rate ($10.00), the insert passes.
INSERT INTO bookings (booking_id, member_id, game_id, start_time, status)
VALUES (103, 5, 4, DATE_SUB(NOW(), INTERVAL 45 MINUTE), 'Ongoing');
