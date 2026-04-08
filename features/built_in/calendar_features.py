import pandas as pd
from features.base import BaseFeatureTransformer


class CalendarFeatureTransformer(BaseFeatureTransformer):
    """Creates calendar-based features from timestamps."""

    def __init__(self, include_holidays: bool = False, country: str = "US"):
        self.include_holidays = include_holidays
        self.country = country
        self.feature_names_ = []

    def fit(self, df: pd.DataFrame) -> "CalendarFeatureTransformer":
        self.feature_names_ = [
            "day_of_week",
            "month",
            "quarter",
            "day_of_year",
        ]
        if self.include_holidays:
            self.feature_names_.append("is_holiday")
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result["day_of_week"] = result["timestamp"].dt.dayofweek
        result["month"] = result["timestamp"].dt.month
        result["quarter"] = result["timestamp"].dt.quarter
        result["day_of_year"] = result["timestamp"].dt.dayofyear

        if self.include_holidays:
            try:
                import holidays
                holiday_calendar = holidays.country_holidays(self.country)
                result["is_holiday"] = result["timestamp"].dt.date.isin(holiday_calendar).astype(int)
            except ImportError:
                result["is_holiday"] = 0

        return result

    def get_feature_names(self) -> list:
        return self.feature_names_
