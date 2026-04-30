-- ============================================================
-- SoulSync AI - MySQL Finance Schema
-- Database: soulsync_finance
-- Engine: InnoDB, charset utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS soulsync_finance
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE soulsync_finance;

-- ─── Wallets ─────────────────────────────────────────────
-- One wallet per user. Stores current balance.
CREATE TABLE IF NOT EXISTS wallets (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id     VARCHAR(100)    NOT NULL,
    balance     DECIMAL(18, 2)  NOT NULL DEFAULT 0.00,
    currency    VARCHAR(10)     NOT NULL DEFAULT 'INR',
    created_at  DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at  DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    UNIQUE KEY uq_wallets_user_id (user_id),
    KEY idx_wallets_user_id (user_id),

    CONSTRAINT chk_wallets_balance CHECK (balance >= 0),
    CONSTRAINT chk_wallets_currency CHECK (CHAR_LENGTH(currency) BETWEEN 1 AND 10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='One wallet per user — stores current balance';


-- ─── Transactions ─────────────────────────────────────────
-- Immutable ledger of all wallet credits and debits.
CREATE TABLE IF NOT EXISTS transactions (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    transaction_id  VARCHAR(100)    NOT NULL,
    user_id         VARCHAR(100)    NOT NULL,
    type            ENUM('credit', 'debit') NOT NULL,
    amount          DECIMAL(18, 2)  NOT NULL,
    currency        VARCHAR(10)     NOT NULL DEFAULT 'INR',
    description     TEXT            NOT NULL DEFAULT '',
    reference_id    VARCHAR(200)    NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'success',
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    UNIQUE KEY uq_transactions_id (transaction_id),
    KEY idx_transactions_user_id (user_id),
    KEY idx_transactions_created_at (created_at),
    KEY idx_transactions_type (type),

    CONSTRAINT fk_transactions_wallet
        FOREIGN KEY (user_id) REFERENCES wallets (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT chk_transactions_amount CHECK (amount > 0),
    CONSTRAINT chk_transactions_status CHECK (
        status IN ('success', 'failed', 'pending', 'reversed')
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Immutable ledger of all wallet credits and debits';


-- ─── Subscription Plans ───────────────────────────────────
-- Available plans managed by admins.
CREATE TABLE IF NOT EXISTS subscription_plans (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    plan_id         VARCHAR(100)    NOT NULL,
    name            VARCHAR(100)    NOT NULL,
    price           DECIMAL(10, 2)  NOT NULL DEFAULT 0.00,
    currency        VARCHAR(10)     NOT NULL DEFAULT 'INR',
    duration_days   INT UNSIGNED    NOT NULL DEFAULT 30,
    features        JSON            NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    UNIQUE KEY uq_plans_plan_id (plan_id),
    KEY idx_plans_is_active (is_active),

    CONSTRAINT chk_plans_price CHECK (price >= 0),
    CONSTRAINT chk_plans_duration CHECK (duration_days > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Available subscription plans';


-- ─── User Subscriptions ───────────────────────────────────
-- Active subscription per user (one at a time).
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id         VARCHAR(100)    NOT NULL,
    plan_id         VARCHAR(100)    NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'active',
    started_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    expires_at      DATETIME(6)     NULL,
    auto_renew      TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                    ON UPDATE CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    UNIQUE KEY uq_user_subscription (user_id),
    KEY idx_usub_user_id (user_id),
    KEY idx_usub_plan_id (plan_id),
    KEY idx_usub_status (status),
    KEY idx_usub_expires_at (expires_at),

    CONSTRAINT fk_usub_plan
        FOREIGN KEY (plan_id) REFERENCES subscription_plans (plan_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT chk_usub_status CHECK (
        status IN ('active', 'expired', 'cancelled', 'paused')
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Active subscription per user';


-- ─── Payment History ──────────────────────────────────────
-- Immutable record of every payment attempt.
CREATE TABLE IF NOT EXISTS payment_history (
    id                  INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    payment_id          VARCHAR(100)    NOT NULL,
    user_id             VARCHAR(100)    NOT NULL,
    subscription_id     INT UNSIGNED    NULL,
    amount              DECIMAL(18, 2)  NOT NULL,
    currency            VARCHAR(10)     NOT NULL DEFAULT 'INR',
    payment_method      VARCHAR(50)     NOT NULL DEFAULT 'wallet',
    status              VARCHAR(20)     NOT NULL DEFAULT 'pending',
    gateway_response    JSON            NULL,
    created_at          DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_id (payment_id),
    KEY idx_payment_user_id (user_id),
    KEY idx_payment_subscription_id (subscription_id),
    KEY idx_payment_status (status),
    KEY idx_payment_created_at (created_at),

    CONSTRAINT fk_payment_subscription
        FOREIGN KEY (subscription_id) REFERENCES user_subscriptions (id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT chk_payment_amount CHECK (amount > 0),
    CONSTRAINT chk_payment_status CHECK (
        status IN ('success', 'failed', 'pending', 'refunded')
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Immutable record of every payment attempt';


-- ─── Seed: Default Plans ──────────────────────────────────
INSERT IGNORE INTO subscription_plans
    (plan_id, name, price, currency, duration_days, features, is_active)
VALUES
    ('plan_free',    'Free',    0.00,   'INR', 30,
     '{"messages_per_day": 20, "memory_days": 7,  "voice": false, "analytics": false}', 1),
    ('plan_pro',     'Pro',     299.00, 'INR', 30,
     '{"messages_per_day": 200, "memory_days": 90, "voice": true,  "analytics": true}',  1),
    ('plan_premium', 'Premium', 599.00, 'INR', 30,
     '{"messages_per_day": -1,  "memory_days": -1,  "voice": true,  "analytics": true, "priority_support": true}', 1);
