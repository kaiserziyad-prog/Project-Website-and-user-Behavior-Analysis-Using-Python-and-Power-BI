"""Synthetic website-traffic data generation. All parameters come from ``config``."""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import config


def _normalise(weights: List[float]) -> List[float]:
    """Scale weights so that they sum to one."""
    total = sum(weights)
    return [w / total for w in weights]


def bounce_probability(device: str, source: str) -> float:
    """Return the probability that a session from this device/source bounces."""
    probability = config.BASE_BOUNCE_PROBABILITY
    probability += config.BOUNCE_DEVICE_ADJUSTMENT.get(device, 0.0)
    probability += config.BOUNCE_SOURCE_ADJUSTMENT.get(source, 0.0)
    low, high = config.BOUNCE_PROBABILITY_RANGE
    return max(low, min(high, probability))


def simulate_engagement(device: str) -> Tuple[int, int]:
    """Draw (page_views, duration_seconds) for a non-bounced session."""
    profile = config.ENGAGEMENT_PROFILES.get(device, config.ENGAGEMENT_PROFILES["default"])
    mean, std, low, high = profile["page_views"]
    page_views = int(np.clip(np.random.normal(mean, std), low, high))
    mean, std, low, high = profile["duration"]
    duration = int(np.clip(np.random.normal(mean, std), low, high))
    return page_views, duration


def conversion_probability(device: str, source: str, page_views: int) -> float:
    """Return the probability that an engaged session converts."""
    probability = config.CONVERSION_SOURCE_PROBABILITY.get(source, config.DEFAULT_CONVERSION_PROBABILITY)
    probability *= config.CONVERSION_DEVICE_MULTIPLIER.get(device, 1.0)
    if page_views >= config.CONVERSION_HIGH_ENGAGEMENT_PAGE_VIEWS:
        probability *= config.CONVERSION_HIGH_ENGAGEMENT_MULTIPLIER
    return probability


def simulate_revenue() -> float:
    """Draw an order value, clipped to the configured range."""
    value = round(float(np.random.gamma(shape=config.REVENUE_GAMMA_SHAPE,
                                        scale=config.REVENUE_GAMMA_SCALE)), 2)
    low, high = config.REVENUE_RANGE
    return max(low, min(high, value))


def generate_session(index: int, user_pool: List[str], start_date: datetime,
                     num_days: int) -> Dict[str, object]:
    """Generate one session record (``index`` is 1-based)."""
    sources = [s[0] for s in config.GENERATOR_SOURCES]
    mediums = [s[1] for s in config.GENERATOR_SOURCES]
    source_weights = [s[2] for s in config.GENERATOR_SOURCES]
    hourly_weights = _normalise(config.GENERATOR_HOURLY_WEIGHTS)

    session_id = f"{config.GENERATOR_SESSION_PREFIX}{config.GENERATOR_SESSION_ID_START + index}"
    user_id = random.choice(user_pool)
    session_date = start_date + timedelta(days=random.randint(0, num_days - 1))
    hour = int(np.random.choice(range(len(hourly_weights)), p=hourly_weights))
    source_index = np.random.choice(len(sources), p=source_weights)
    source, medium = sources[source_index], mediums[source_index]
    device = np.random.choice(config.GENERATOR_DEVICES, p=config.GENERATOR_DEVICE_WEIGHTS)
    browser = np.random.choice(config.GENERATOR_BROWSERS, p=config.GENERATOR_BROWSER_WEIGHTS)
    country = np.random.choice(config.GENERATOR_COUNTRIES, p=config.GENERATOR_COUNTRY_WEIGHTS)

    bounced = random.random() < bounce_probability(device, source)
    conversions, revenue = 0, 0.0
    if bounced:
        page_views = 1
        duration = random.randint(*config.BOUNCE_DURATION_RANGE)
    else:
        page_views, duration = simulate_engagement(device)
        if random.random() < conversion_probability(device, source, page_views):
            conversions, revenue = 1, simulate_revenue()

    return {
        config.COL_DATE: session_date.strftime(config.DATE_FORMAT),
        config.COL_HOUR: hour,
        config.COL_SESSION: session_id,
        config.COL_USER: user_id,
        config.COL_SOURCE: source,
        config.COL_MEDIUM: medium,
        config.COL_DEVICE: device,
        config.COL_BROWSER: browser,
        config.COL_COUNTRY: country,
        config.COL_PAGE_VIEWS: page_views,
        config.COL_DURATION: duration,
        config.COL_BOUNCE: int(bounced),
        config.COL_CONVERSIONS: conversions,
        config.COL_REVENUE: revenue,
    }


def inject_quality_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Add duplicate rows and stray whitespace so the cleaning step has work to do."""
    duplicates = df.sample(config.GENERATOR_DUPLICATE_ROWS, random_state=config.GENERATOR_QUALITY_SEED)
    df = pd.concat([df, duplicates], ignore_index=True)
    idx = df.sample(config.GENERATOR_WHITESPACE_ROWS, random_state=config.GENERATOR_QUALITY_SEED).index
    df.loc[idx, config.COL_SOURCE] = df.loc[idx, config.COL_SOURCE] + " "
    return df


def generate_website_traffic_data(num_records: int = config.DEFAULT_GENERATED_RECORDS,
                                  random_seed: int = config.DEFAULT_RANDOM_SEED) -> pd.DataFrame:
    """Generate a reproducible synthetic dataset (including deliberate quality issues)."""
    random.seed(random_seed)
    np.random.seed(random_seed)
    start_date = datetime.fromisoformat(config.GENERATOR_START_DATE)
    end_date = datetime.fromisoformat(config.GENERATOR_END_DATE)
    num_days = (end_date - start_date).days + 1
    user_pool = [f"{config.GENERATOR_USER_PREFIX}{config.GENERATOR_USER_ID_START + i}"
                 for i in range(config.GENERATOR_NUM_USERS)]
    records = [generate_session(i, user_pool, start_date, num_days)
               for i in range(1, num_records + 1)]
    return inject_quality_issues(pd.DataFrame(records))
