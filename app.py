import streamlit as st
import pymysql
import pandas as pd
import datetime
import os
import subprocess

# Set page configuration with dark mode preferences
st.set_page_config(
    page_title="SQL Skills Showcase - Games Member Club",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS for styling and visuals
st.markdown("""
<style>
    /* Gradient headers and general theme adjustments */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #8A2387, #E94057);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .subtitle {
        font-size: 1.2rem;
        color: #8892b0;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    /* Status card styling */
    .status-card {
        padding: 1.5rem;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        backdrop-filter: blur(4px);
        margin-bottom: 1.5rem;
    }
    .status-online {
        color: #4CAF50;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .status-offline {
        color: #F44336;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    /* Section containers */
    .section-card {
        padding: 2rem;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 2rem;
    }
    /* Table headers styling */
    .view-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8f9fa;
        border-bottom: 2px solid #8A2387;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    /* Database badge styling */
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-bronze { background-color: #CD7F32; color: white; }
    .badge-silver { background-color: #C0C0C0; color: black; }
    .badge-gold { background-color: #FFD700; color: black; }
    .badge-vip { background-color: #E0115F; color: white; }
    
    /* Code block styling */
    .sql-code {
        font-family: 'Courier New', Courier, monospace;
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 10px;
        border-radius: 6px;
        border-left: 4px solid #8A2387;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Database Connection Utility
DB_SOCKET = "/Users/vishvatejaguduguntla/Game_membership project/database/mysql_socket/mysql.sock"
DB_NAME = "games_member_club"

def get_connection():
    try:
        # Connect via UNIX socket for macOS local server
        conn = pymysql.connect(
            user='root',
            unix_socket=DB_SOCKET,
            db=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, None
    except Exception as e:
        # Fallback to TCP if socket fails or isn't used
        try:
            conn = pymysql.connect(
                host='127.0.0.1',
                port=33066,
                user='root',
                db=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn, None
        except Exception as e2:
            return None, f"Socket error: {str(e)}\nTCP error: {str(e2)}"

# Execute Query helper
def run_query(query, params=None):
    conn, err = get_connection()
    if err:
        return None, err
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if query.strip().lower().startswith(('select', 'show', 'desc')):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
        conn.close()
        return result, None
    except Exception as e:
        if conn:
            conn.close()
        return None, str(e)

# Multi-statement runner helper (e.g. for transactions)
def run_transaction(queries_and_params):
    conn, err = get_connection()
    if err:
        return None, err
    try:
        results = []
        with conn.cursor() as cursor:
            for q, p in queries_and_params:
                cursor.execute(q, p)
                results.append(cursor.rowcount)
            conn.commit()
        conn.close()
        return results, None
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return None, str(e)

# Helper to check if DB server is alive
def check_db_status():
    conn, err = get_connection()
    if conn:
        conn.close()
        return True
    return False

# Header
st.markdown('<div class="main-title">Games Member Club</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">An Interactive SQL Skills & Triggers Showcase Dashboard</div>', unsafe_allow_html=True)

# Database Control Panel in Sidebar
st.sidebar.markdown("### 🖥️ Database Engine Status")
is_running = check_db_status()

if is_running:
    st.sidebar.markdown('<div class="status-online">● Live & Connected</div>', unsafe_allow_html=True)
    st.sidebar.caption("MySQL 9.7.0 serving on port 33066 via Unix Socket")
    
    # Quick reset database button
    if st.sidebar.button("🔄 Reload Schema & Seed Data"):
        with st.spinner("Resetting database..."):
            res = subprocess.run(["./db_setup.sh"], capture_output=True, text=True)
            if res.returncode == 0:
                st.sidebar.success("Database reset successfully!")
                st.rerun()
            else:
                st.sidebar.error(f"Error resetting: {res.stderr}")
else:
    st.sidebar.markdown('<div class="status-offline">● Stopped / Offline</div>', unsafe_allow_html=True)
    st.sidebar.warning("Could not connect to custom MySQL server on port 33066.")
    
    if st.sidebar.button("⚡ Start Database Server"):
        with st.spinner("Starting MySQL..."):
            res = subprocess.run(["./db_setup.sh"], capture_output=True, text=True)
            if res.returncode == 0:
                st.sidebar.success("Database started successfully!")
                st.rerun()
            else:
                st.sidebar.error(f"Failed to start: {res.stderr}")

# Stop server button
if is_running:
    if st.sidebar.button("🛑 Stop Database Server", type="secondary"):
        with st.spinner("Stopping MySQL..."):
            res = subprocess.run(["./db_stop.sh"], capture_output=True, text=True)
            st.sidebar.info("Database stopped.")
            st.rerun()

st.sidebar.markdown("---")

# Navigation Tabs
menu_selection = st.sidebar.radio(
    "Navigate Application",
    ["🏠 Home & Overview", "⚡ Scenario Trigger Runner", "📊 Analytical Views", "💻 SQL Console Sandbox"]
)

# Render view based on selection
if not is_running:
    st.error("🚨 Database server is currently offline. Please click the **'Start Database Server'** button in the sidebar to run the application.")
else:
    # ----------------------------------------------------
    # TAB 1: HOME & OVERVIEW
    # ----------------------------------------------------
    if menu_selection == "🏠 Home & Overview":
        col1, col2, col3, col4 = st.columns(4)
        
        # Pull Quick Stats
        m_count, _ = run_query("SELECT COUNT(*) as count FROM members")
        g_count, _ = run_query("SELECT COUNT(*) as count FROM games")
        active_count, _ = run_query("SELECT COUNT(*) as count FROM bookings WHERE status = 'Ongoing'")
        rev_count, _ = run_query("SELECT SUM(total_cost) as total FROM bookings WHERE status = 'Completed'")
        
        with col1:
            st.metric("Total Club Members", m_count[0]['count'] if m_count else 0)
        with col2:
            st.metric("Gaming Stations", g_count[0]['count'] if g_count else 0)
        with col3:
            st.metric("Active Sessions", active_count[0]['count'] if active_count else 0)
        with col4:
            st.metric("Lifetime Session Revenue", f"${rev_count[0]['total']:.2f}" if rev_count and rev_count[0]['total'] else "$0.00")
            
        st.markdown("### 🎮 Database Design Objective")
        st.write(
            "This application acts as a test bench for the SQL database schema defined in `schema.sql`. "
            "By implementing key business rules at the database engine level (via check constraints, foreign keys, and triggers), "
            "we guarantee data integrity and auditability regardless of which external application connects to the DB."
        )
        
        st.markdown("### 🛠️ Advanced SQL Features Implemented")
        
        st.markdown("""
        <div class="status-card">
            <h4>1. Automatic Wallet Balance & Loyalty Tier Calculator</h4>
            <p>Every time a transaction is inserted into the <code>wallet_transactions</code> table, the <code>after_transaction_insert</code> trigger fires. It:</p>
            <ul>
                <li>Updates the member's current <code>wallet_balance</code>.</li>
                <li>Calculates their lifetime deposits.</li>
                <li>Automatically upgrades their <code>membership_tier</code> (Bronze, Silver, Gold, or VIP) based on lifetime deposits.</li>
            </ul>
        </div>
        
        <div class="status-card">
            <h4>2. Insufficient Wallet Balance Guard</h4>
            <p>To start playing, a member must have a wallet balance high enough to cover at least 1 hour of playing on the chosen game. The <code>before_booking_insert</code> trigger enforces this rule, throwing a database signal state <code>45000</code> if a booking fails to meet the requirement.</p>
        </div>

        <div class="status-card">
            <h4>3. Automated Session Cost & Payment Ledger Generation</h4>
            <p>When a booking is closed (status transitions to 'Completed'), two database triggers work in lockstep:</p>
            <ul>
                <li><code>before_booking_update</code>: Automatically computes the elapsed duration, multiplies it by the game's hourly rate, and writes the <code>total_cost</code>.</li>
                <li><code>after_booking_complete</code>: Automatically inserts a payment transaction into <code>wallet_transactions</code>, which cascades to deduct the member's wallet balance.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📂 Active Database Tables")
        tabs = st.tabs(["members", "games", "bookings", "wallet_transactions"])
        
        with tabs[0]:
            df, _ = run_query("SELECT id, name, age, phone, wallet_balance, membership_tier, join_date FROM members")
            st.dataframe(pd.DataFrame(df), use_container_width=True)
        with tabs[1]:
            df, _ = run_query("SELECT game_id, title, genre, platform, hourly_rate, status FROM games")
            st.dataframe(pd.DataFrame(df), use_container_width=True)
        with tabs[2]:
            df, _ = run_query("SELECT booking_id, member_id, game_id, start_time, end_time, total_cost, status FROM bookings")
            st.dataframe(pd.DataFrame(df), use_container_width=True)
        with tabs[3]:
            df, _ = run_query("SELECT transaction_id, member_id, amount, transaction_type, transaction_date, description FROM wallet_transactions")
            st.dataframe(pd.DataFrame(df), use_container_width=True)

    # ----------------------------------------------------
    # TAB 2: SCENARIO TRIGGER RUNNER
    # ----------------------------------------------------
    elif menu_selection == "⚡ Scenario Trigger Runner":
        st.markdown("### ⚡ Test Database Triggers in Real-Time")
        st.write("Interact with the UI inputs below to trigger database-level procedures and observe the direct consequences on other tables.")
        
        scenario_tab = st.tabs([
            "💰 Scenario 1: Deposits & Loyalty Upgrades",
            "🚫 Scenario 2: Insufficient Balance Guard",
            "⏱️ Scenario 3: Complete Booking & Auto-Billing"
        ])
        
        # --- SCENARIO 1: DEPOSITS & UPGRADES ---
        with scenario_tab[0]:
            st.markdown("#### Scenario 1: Deposit Money & Upgrade Membership Tier")
            st.write(
                "When you insert a deposit transaction, the database automatically: "
                "1. Adds the amount to the user's wallet. "
                "2. Recalculates their lifetime deposits. "
                "3. Upgrades their loyalty tier if threshold is reached."
            )
            
            # Form inputs
            members_list, _ = run_query("SELECT id, name, wallet_balance, membership_tier FROM members")
            m_options = {f"{m['name']} (Current: ${m['wallet_balance']:.2f}, Tier: {m['membership_tier']})": m['id'] for m in members_list}
            selected_m_label = st.selectbox("Select Member for Deposit", list(m_options.keys()), key="s1_mem")
            selected_m_id = m_options[selected_m_label]
            
            deposit_amount = st.number_input("Deposit Amount ($)", min_value=1.0, max_value=1000.0, value=50.0, step=10.0, key="s1_amt")
            dep_description = st.text_input("Transaction Description", "Mobile App Top-up", key="s1_desc")
            
            if st.button("Simulate Deposit Transaction", type="primary"):
                # Run insert query
                q = """
                    INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)
                    VALUES (%s, %s, 'Deposit', %s)
                """
                res, err = run_query(q, (selected_m_id, deposit_amount, dep_description))
                
                if err:
                    st.error(f"Database Error: {err}")
                else:
                    st.success(f"Successfully inserted deposit transaction of ${deposit_amount:.2f}!")
                    
                    # Query updated details
                    m_updated, _ = run_query("SELECT name, wallet_balance, membership_tier FROM members WHERE id = %s", (selected_m_id,))
                    t_sum, _ = run_query("SELECT SUM(amount) as total FROM wallet_transactions WHERE member_id = %s AND transaction_type = 'Deposit'", (selected_m_id,))
                    
                    st.markdown("##### 🔍 Database Cascade Updates Result")
                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        st.markdown("**Executed SQL Query:**")
                        st.code(f"INSERT INTO wallet_transactions (member_id, amount, transaction_type, description)\nVALUES ({selected_m_id}, {deposit_amount:.2f}, 'Deposit', '{dep_description}');", language="sql")
                        st.markdown("**Fired Trigger Code:**")
                        st.code("""CREATE TRIGGER after_transaction_insert
AFTER INSERT ON wallet_transactions
FOR EACH ROW
BEGIN
    -- 1. Apply transaction amount directly to user's wallet
    UPDATE members SET wallet_balance = wallet_balance + NEW.amount WHERE id = NEW.member_id;
    -- 2. Calculate lifetime deposits to determine loyalty tiers
    SELECT COALESCE(SUM(amount), 0) INTO total_deposited FROM wallet_transactions
    WHERE member_id = NEW.member_id AND transaction_type = 'Deposit';
    -- 3. Apply tier upgrades based on lifetime deposits...
END""", language="sql")
                    with res_col2:
                        st.markdown("**New Wallet Balance:**")
                        st.subheader(f"${m_updated[0]['wallet_balance']:.2f}")
                        st.markdown("**New Membership Tier:**")
                        st.subheader(m_updated[0]['membership_tier'])
                        st.markdown(f"**Total Lifetime Deposits:** ${t_sum[0]['total']:.2f}")
            
        # --- SCENARIO 2: INSUFFICIENT BALANCE GUARD ---
        with scenario_tab[1]:
            st.markdown("#### Scenario 2: Insufficient Funds Guard")
            st.write(
                "To prevent members from using stations they cannot afford, the database blocks ongoing booking inserts "
                "if their current wallet balance is less than the hourly rate of the selected game station."
            )
            
            # Select member
            members_list2, _ = run_query("SELECT id, name, wallet_balance FROM members")
            m_options2 = {f"{m['name']} (Balance: ${m['wallet_balance']:.2f})": (m['id'], m['wallet_balance']) for m in members_list2}
            selected_m_label2 = st.selectbox("Select Member to Book", list(m_options2.keys()), key="s2_mem")
            m_id, m_bal = m_options2[selected_m_label2]
            
            # Select game station
            games_list, _ = run_query("SELECT game_id, title, platform, hourly_rate FROM games WHERE status = 'Available'")
            if not games_list:
                st.warning("No gaming stations are currently marked as 'Available'. Run 'Reload Schema & Seed Data' in the sidebar to reset station availability.")
                g_options = {}
            else:
                g_options = {f"{g['title']} on {g['platform']} (Rate: ${g['hourly_rate']:.2f}/hr)": (g['game_id'], g['hourly_rate']) for g in games_list}
            
            if g_options:
                selected_g_label = st.selectbox("Select Game Station", list(g_options.keys()), key="s2_game")
                g_id, g_rate = g_options[selected_g_label]
                
                # Check condition visually
                affords = m_bal >= g_rate
                if affords:
                    st.info(f"💡 This member has enough funds (${m_bal:.2f} >= ${g_rate:.2f}). The booking will succeed.")
                else:
                    st.warning(f"⚠️ This member has insufficient funds (${m_bal:.2f} < ${g_rate:.2f}). The database trigger will BLOCK this transaction.")
                
                if st.button("Attempt Booking Transaction", type="primary"):
                    q = """
                        INSERT INTO bookings (member_id, game_id, start_time, status)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, 'Ongoing')
                    """
                    res, err = run_query(q, (m_id, g_id))
                    
                    if err:
                        st.markdown("##### 🚫 Database Transaction Rejected!")
                        st.error(f"SQLSTATE Signal Raised: {err}")
                        st.markdown("""
                        This operation was rejected by the database trigger:
                        ```sql
                        CREATE TRIGGER before_booking_insert
                        BEFORE INSERT ON bookings
                        FOR EACH ROW
                        BEGIN
                            -- Fetch wallet balance & game rate...
                            IF NEW.status = 'Ongoing' AND member_bal < game_rate THEN
                                SIGNAL SQLSTATE '45000'
                                SET MESSAGE_TEXT = 'Insufficient wallet balance. Members must have at least 1 hour of the game rate to start playing.';
                            END IF;
                        END
                        ```
                        """)
                    else:
                        st.success("🎉 Booking successfully completed! The member had sufficient funds.")
                        st.balloons()
            
        # --- SCENARIO 3: COMPLETE BOOKING & AUTO-BILLING ---
        with scenario_tab[2]:
            st.markdown("#### Scenario 3: Complete Session & Auto-Bill Wallet")
            st.write(
                "When an ongoing session is completed, updating its status to 'Completed' triggers a chain of events: "
                "1. `before_booking_update` automatically computes total elapsed time and multiplies it by hourly rate. "
                "2. `after_booking_complete` logs a payment transaction in `wallet_transactions` ledger. "
                "3. `after_transaction_insert` subtracts the payment from the member's wallet balance."
            )
            
            # Query active ongoing bookings
            active_b, _ = run_query("""
                SELECT b.booking_id, m.name as member_name, g.title as game_title, g.hourly_rate, b.start_time 
                FROM bookings b
                JOIN members m ON b.member_id = m.id
                JOIN games g ON b.game_id = g.game_id
                WHERE b.status = 'Ongoing'
            """)
            
            if not active_b:
                st.info("No ongoing bookings are active. You can start one using the 'Insufficient Balance Guard' tab above with a member who has sufficient funds.")
            else:
                b_options = {f"Booking #{b['booking_id']} - {b['member_name']} playing {b['game_title']} (Started: {b['start_time'].strftime('%H:%M:%S')})": b for b in active_b}
                selected_b_label = st.selectbox("Select Active Booking to Complete", list(b_options.keys()))
                booking_data = b_options[selected_b_label]
                
                # Input custom simulation duration or use actual duration
                duration_mode = st.radio("Simulation Duration Mode", ["Simulate Custom Duration (Hours)", "Use Actual Elapsed Time"])
                
                if duration_mode == "Simulate Custom Duration (Hours)":
                    sim_hours = st.number_input("Duration (Hours)", min_value=0.1, max_value=24.0, value=2.5, step=0.5)
                    # Calculate simulated end_time
                    end_time_val = booking_data['start_time'] + datetime.timedelta(seconds=int(sim_hours * 3600))
                else:
                    end_time_val = datetime.datetime.now()
                    sim_hours = (end_time_val - booking_data['start_time']).total_seconds() / 3600.0
                
                st.write(f"Estimated Cost: **${sim_hours * booking_data['hourly_rate']:.2f}** ({sim_hours:.2f} hrs @ ${booking_data['hourly_rate']:.2f}/hr)")
                
                if st.button("Complete Booking Session", type="primary"):
                    q = """
                        UPDATE bookings 
                        SET status = 'Completed', end_time = %s 
                        WHERE booking_id = %s
                    """
                    res, err = run_query(q, (end_time_val, booking_data['booking_id']))
                    
                    if err:
                        st.error(f"Database Error: {err}")
                    else:
                        st.success("Session completed and closed!")
                        
                        # Fetch the calculated results
                        b_res, _ = run_query("""
                            SELECT total_cost, TIMESTAMPDIFF(SECOND, start_time, end_time) as sec
                            FROM bookings WHERE booking_id = %s
                        """, (booking_data['booking_id'],))
                        
                        trans_res, _ = run_query("""
                            SELECT transaction_id, amount, description FROM wallet_transactions 
                            WHERE description LIKE CONCAT('%%Booking ID ', %s, '%%')
                        """, (booking_data['booking_id'],))
                        
                        st.markdown("##### 🔍 Database Cascade Updates Result")
                        res_col1, res_col2 = st.columns(2)
                        with res_col1:
                            st.markdown("**Executed SQL Update:**")
                            st.code(f"UPDATE bookings SET status = 'Completed', end_time = '{end_time_val.strftime('%Y-%m-%d %H:%M:%S')}' WHERE booking_id = {booking_data['booking_id']};", language="sql")
                            st.markdown("**Calculated Session Time:**")
                            sec = b_res[0]['sec'] if b_res else 0
                            st.write(f"⏱️ {sec / 3600.0:.2f} Hours ({sec} seconds elapsed)")
                        with res_col2:
                            st.markdown("**Auto-Calculated Booking Cost:**")
                            st.subheader(f"${b_res[0]['total_cost']:.2f}" if b_res else "$0.00")
                            
                            st.markdown("**Auto-Generated Ledger Transaction:**")
                            if trans_res:
                                st.write(f"📝 Transaction #{trans_res[0]['transaction_id']}")
                                st.write(f"💵 Amount: **{trans_res[0]['amount']:.2f}**")
                                st.caption(trans_res[0]['description'])
                            else:
                                st.write("No transaction found.")

    # ----------------------------------------------------
    # TAB 3: ANALYTICAL VIEWS
    # ----------------------------------------------------
    elif menu_selection == "📊 Analytical Reports":
        pass  # Just a placeholder for menu structure. Code handles matching selection correctly below.

    if menu_selection == "📊 Analytical Views":
        st.markdown("### 📊 Analytical Database Views")
        st.write("These views are calculated directly in the database engine using complex joins and aggregations, providing standard reporting queries in real-time.")
        
        view_tabs = st.tabs([
            "🟢 View A: Active Sessions",
            "💳 View B: Member Financials",
            "📈 View C: Game Performance"
        ])
        
        with view_tabs[0]:
            st.markdown("#### `view_active_sessions`")
            st.caption("Shows players currently on stations, their platform, and duration.")
            df, err = run_query("SELECT * FROM view_active_sessions")
            if err:
                st.error(err)
            else:
                if not df:
                    st.info("No active players right now.")
                else:
                    st.dataframe(pd.DataFrame(df), use_container_width=True)
            
            with st.expander("Show View SQL Definition"):
                st.code("""CREATE VIEW view_active_sessions AS
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
WHERE b.status = 'Ongoing';""", language="sql")
                
        with view_tabs[1]:
            st.markdown("#### `view_member_financials`")
            st.caption("Financial ledger summary for each member: total deposits, payments, and current balance.")
            df, err = run_query("SELECT * FROM view_member_financials")
            if err:
                st.error(err)
            else:
                pdf = pd.DataFrame(df)
                st.dataframe(pdf, use_container_width=True)
                
                # Chart
                if not pdf.empty:
                    st.markdown("##### Spending vs Current Balance")
                    chart_data = pdf[['member_name', 'total_spent', 'current_balance']].copy()
                    chart_data = chart_data.set_index('member_name')
                    st.bar_chart(chart_data, y=['total_spent', 'current_balance'])
                    
            with st.expander("Show View SQL Definition"):
                st.code("""CREATE VIEW view_member_financials AS
SELECT 
    m.id AS member_id,
    m.name AS member_name,
    m.membership_tier,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'Deposit' THEN t.amount ELSE 0 END), 0.00) AS total_deposited,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'Payment' THEN ABS(t.amount) ELSE 0 END), 0.00) AS total_spent,
    m.wallet_balance AS current_balance
FROM members m
LEFT JOIN wallet_transactions t ON m.id = t.member_id
GROUP BY m.id, m.name, m.membership_tier, m.wallet_balance;""", language="sql")
                
        with view_tabs[2]:
            st.markdown("#### `view_game_performance`")
            st.caption("Aggregated usage and revenue stats for each gaming station/platform.")
            df, err = run_query("SELECT * FROM view_game_performance")
            if err:
                st.error(err)
            else:
                pdf = pd.DataFrame(df)
                st.dataframe(pdf, use_container_width=True)
                
                if not pdf.empty:
                    st.markdown("##### Revenue & Bookings by Game Title")
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        # Revenue chart
                        st.subheader("Game Revenue ($)")
                        rev_chart = pdf[['game_title', 'total_revenue']].copy().set_index('game_title')
                        st.bar_chart(rev_chart)
                    with chart_col2:
                        # Bookings count chart
                        st.subheader("Total Bookings Count")
                        bk_chart = pdf[['game_title', 'total_bookings']].copy().set_index('game_title')
                        st.bar_chart(bk_chart)
                        
            with st.expander("Show View SQL Definition"):
                st.code("""CREATE VIEW view_game_performance AS
SELECT 
    g.game_id,
    g.title AS game_title,
    g.platform,
    COUNT(b.booking_id) AS total_bookings,
    ROUND(COALESCE(SUM(TIMESTAMPDIFF(SECOND, b.start_time, b.end_time) / 3600.0), 0), 1) AS total_hours_played,
    COALESCE(SUM(b.total_cost), 0.00) AS total_revenue
FROM games g
LEFT JOIN bookings b ON g.game_id = b.game_id AND b.status = 'Completed'
GROUP BY g.game_id, g.title, g.platform;""", language="sql")

    # ----------------------------------------------------
    # TAB 4: SQL CONSOLE SANDBOX
    # ----------------------------------------------------
    elif menu_selection == "💻 SQL Console Sandbox":
        st.markdown("### 💻 SQL Editor Console")
        st.write("Write custom queries and run them directly against the live database instance on port 33066.")
        
        # Grid layout: Console on left, schema schema reference on right
        sandbox_col1, sandbox_col2 = st.columns([3, 1])
        
        with sandbox_col1:
            sql_input = st.text_area(
                "Write SQL Statement",
                "SELECT * FROM view_member_financials WHERE membership_tier = 'Silver' OR membership_tier = 'Gold';",
                height=180
            )
            
            col_btn1, col_btn2 = st.columns([1, 4])
            run_btn = col_btn1.button("Execute SQL Query", type="primary")
            
            if run_btn:
                if not sql_input.strip():
                    st.warning("Please enter a query to run.")
                else:
                    with st.spinner("Executing..."):
                        # Check if query is safe (read-only restriction or normal execution)
                        res, err = run_query(sql_input)
                        
                        if err:
                            st.error(f"❌ SQL Execution Error:\n{err}")
                        else:
                            if isinstance(res, list):
                                if not res:
                                    st.info("Query returned 0 rows.")
                                else:
                                    df = pd.DataFrame(res)
                                    st.success(f"Successfully executed query! Returned {len(df)} rows.")
                                    st.dataframe(df, use_container_width=True)
                            else:
                                st.success(f"Statement executed successfully! Affected rows: {res}")
                                
        with sandbox_col2:
            st.markdown("#### 📂 Schema Directory")
            
            with st.expander("👥 Table: `members`"):
                st.caption("""- id (INT, PK)
- name (VARCHAR)
- age (INT)
- phone (VARCHAR, UNIQUE)
- wallet_balance (DECIMAL)
- membership_tier (VARCHAR)
- join_date (DATETIME)""")
                
            with st.expander("🎮 Table: `games`"):
                st.caption("""- game_id (INT, PK)
- title (VARCHAR)
- genre (VARCHAR)
- platform (VARCHAR)
- hourly_rate (DECIMAL)
- status (VARCHAR)""")
                
            with st.expander("📅 Table: `bookings`"):
                st.caption("""- booking_id (INT, PK)
- member_id (INT, FK)
- game_id (INT, FK)
- start_time (DATETIME)
- end_time (DATETIME)
- total_cost (DECIMAL)
- status (VARCHAR)""")
                
            with st.expander("📝 Table: `wallet_transactions`"):
                st.caption("""- transaction_id (INT, PK)
- member_id (INT, FK)
- amount (DECIMAL)
- transaction_type (VARCHAR)
- transaction_date (DATETIME)
- description (VARCHAR)""")
                
            st.markdown("#### 📊 Analytical Views")
            st.caption("""- `view_active_sessions`
- `view_member_financials`
- `view_game_performance`""")
