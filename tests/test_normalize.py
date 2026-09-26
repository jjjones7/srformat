import unittest
from datetime import date

from srformat.normalize import (
    ParseError,
    normalize_date,
    normalize_ease,
    normalize_interval,
    normalize_rating,
    normalize_record,
    split_fields,
)


class SplitFieldsTests(unittest.TestCase):
    def test_comma_separated(self):
        self.assertEqual(
            split_fields("2024-01-05,3,2.5,good"),
            ["2024-01-05", "3", "2.5", "good"],
        )

    def test_mixed_delimiters(self):
        self.assertEqual(
            split_fields("2024-01-05| 3\t2.5;good"),
            ["2024-01-05", "3", "2.5", "good"],
        )

    def test_trailing_delimiter_is_ignored(self):
        self.assertEqual(
            split_fields("2024-01-05,3,2.5,good,"),
            ["2024-01-05", "3", "2.5", "good"],
        )

    def test_wrong_field_count_raises(self):
        with self.assertRaises(ParseError):
            split_fields("2024-01-05,3,2.5")

    def test_extra_field_raises(self):
        with self.assertRaises(ParseError):
            split_fields("2024-01-05,3,2.5,good,extra")


class NormalizeDateTests(unittest.TestCase):
    def test_iso(self):
        self.assertEqual(normalize_date("2024-01-05"), date(2024, 1, 5))

    def test_iso_single_digit_month_day(self):
        self.assertEqual(normalize_date("2024-1-5"), date(2024, 1, 5))

    def test_slash_form(self):
        self.assertEqual(normalize_date("2024/01/08"), date(2024, 1, 8))

    def test_us_slash_form(self):
        self.assertEqual(normalize_date("01/05/2024"), date(2024, 1, 5))

    def test_day_month_abbrev(self):
        self.assertEqual(normalize_date("5 Jan 2024"), date(2024, 1, 5))

    def test_day_month_full(self):
        self.assertEqual(normalize_date("5 January 2024"), date(2024, 1, 5))

    def test_month_day_comma_year(self):
        self.assertEqual(normalize_date("Jan 5, 2024"), date(2024, 1, 5))

    def test_month_day_year_no_comma(self):
        self.assertEqual(normalize_date("Jan 5 2024"), date(2024, 1, 5))

    def test_full_month_day_comma_year(self):
        self.assertEqual(normalize_date("January 5, 2024"), date(2024, 1, 5))

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(normalize_date("  2024-01-05  "), date(2024, 1, 5))

    def test_unrecognized_raises(self):
        with self.assertRaises(ParseError):
            normalize_date("not a date")

    def test_garbage_after_valid_date_raises(self):
        with self.assertRaises(ParseError):
            normalize_date("2024-01-05 extra")


class NormalizeIntervalTests(unittest.TestCase):
    def test_bare_number_means_days(self):
        self.assertEqual(normalize_interval("10"), 10)

    def test_explicit_days_short(self):
        self.assertEqual(normalize_interval("3d"), 3)

    def test_explicit_days_long(self):
        self.assertEqual(normalize_interval("3 days"), 3)

    def test_weeks(self):
        self.assertEqual(normalize_interval("2w"), 14)
        self.assertEqual(normalize_interval("2 weeks"), 14)

    def test_months_not_eaten_by_mo(self):
        self.assertEqual(normalize_interval("1 month"), 30)
        self.assertEqual(normalize_interval("1mo"), 30)

    def test_years(self):
        self.assertEqual(normalize_interval("1y"), 365)
        self.assertEqual(normalize_interval("1 year"), 365)

    def test_fractional_amount(self):
        self.assertEqual(normalize_interval("1.5mo"), 45)

    def test_iso_duration(self):
        self.assertEqual(normalize_interval("P3D"), 3)
        self.assertEqual(normalize_interval("P7D"), 7)
        self.assertEqual(normalize_interval("P1Y"), 365)
        self.assertEqual(normalize_interval("P1M2D"), 32)

    def test_iso_duration_lowercase(self):
        self.assertEqual(normalize_interval("p3d"), 3)

    def test_unit_is_case_insensitive(self):
        self.assertEqual(normalize_interval("3D"), 3)
        self.assertEqual(normalize_interval("3 DAYS"), 3)

    def test_unrecognized_unit_raises(self):
        with self.assertRaises(ParseError):
            normalize_interval("3 fortnights")

    def test_unrecognized_format_raises(self):
        with self.assertRaises(ParseError):
            normalize_interval("soon")

    def test_zero_raises(self):
        with self.assertRaises(ParseError):
            normalize_interval("0d")

    def test_negative_rejected_by_pattern(self):
        with self.assertRaises(ParseError):
            normalize_interval("-3d")

    def test_bare_p_raises(self):
        with self.assertRaises(ParseError):
            normalize_interval("P")

    def test_iso_zero_duration_raises(self):
        with self.assertRaises(ParseError):
            normalize_interval("P0D")


class NormalizeEaseTests(unittest.TestCase):
    def test_plain_float(self):
        self.assertEqual(normalize_ease("2.5"), 2.5)

    def test_percent_form(self):
        self.assertEqual(normalize_ease("250%"), 2.5)

    def test_bare_hundreds_treated_as_percent(self):
        # nothing exports a multiplier above 10, so 250 means 2.50
        self.assertEqual(normalize_ease("250"), 2.5)

    def test_value_at_threshold_not_scaled(self):
        self.assertEqual(normalize_ease("10"), 10.0)

    def test_whitespace_around_percent(self):
        self.assertEqual(normalize_ease(" 250 % "), 2.5)

    def test_zero_raises(self):
        with self.assertRaises(ParseError):
            normalize_ease("0")

    def test_negative_raises(self):
        with self.assertRaises(ParseError):
            normalize_ease("-1")

    def test_non_numeric_raises(self):
        with self.assertRaises(ParseError):
            normalize_ease("high")


class NormalizeRatingTests(unittest.TestCase):
    def test_word_aliases(self):
        self.assertEqual(normalize_rating("again"), 0)
        self.assertEqual(normalize_rating("hard"), 1)
        self.assertEqual(normalize_rating("good"), 2)
        self.assertEqual(normalize_rating("easy"), 3)

    def test_synonym_aliases(self):
        self.assertEqual(normalize_rating("fail"), 0)
        self.assertEqual(normalize_rating("wrong"), 0)
        self.assertEqual(normalize_rating("forgot"), 0)
        self.assertEqual(normalize_rating("pass"), 2)
        self.assertEqual(normalize_rating("okay"), 2)
        self.assertEqual(normalize_rating("perfect"), 3)

    def test_numeric_aliases(self):
        self.assertEqual(normalize_rating("0"), 0)
        self.assertEqual(normalize_rating("3"), 3)

    def test_case_insensitive(self):
        self.assertEqual(normalize_rating("GOOD"), 2)
        self.assertEqual(normalize_rating(" Easy "), 3)

    def test_unrecognized_raises(self):
        with self.assertRaises(ParseError):
            normalize_rating("meh")


class NormalizeRecordTests(unittest.TestCase):
    def test_full_record(self):
        record = normalize_record("2024-1-5, 3d, 250%, good")
        self.assertEqual(record.due, date(2024, 1, 5))
        self.assertEqual(record.interval_days, 3)
        self.assertEqual(record.ease, 2.5)
        self.assertEqual(record.rating, 2)
        self.assertEqual(record.rating_label, "good")

    def test_as_row(self):
        record = normalize_record("2024-01-08;10;2.5;again")
        self.assertEqual(
            record.as_row(),
            ("2024-01-08", "10", "2.50", "again"),
        )

    def test_bad_field_count_propagates(self):
        with self.assertRaises(ParseError):
            normalize_record("2024-01-05,3,2.5")

    def test_bad_date_propagates(self):
        with self.assertRaises(ParseError):
            normalize_record("not-a-date,3,2.5,good")


if __name__ == "__main__":
    unittest.main()
