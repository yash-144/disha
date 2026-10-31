import unittest
import os
import pandas as pd
import numpy as np

class TestDatasetIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.csv')
        if not os.path.exists(cls.data_path):
            raise FileNotFoundError(f"data.csv not found at {cls.data_path}")
        
        # Read raw header line to test column name anomalies directly on disk
        with open(cls.data_path, 'r', encoding='utf-8') as f:
            cls.raw_header = f.readline()
            
        # Load dataset with pandas
        cls.df = pd.read_csv(cls.data_path, sep=';')

    # 1. Column Names
    def test_column_names_count_and_presence(self):
        """Ensure all 37 columns are present: 36 input features and 1 target."""
        self.assertEqual(len(self.df.columns), 37)
        self.assertIn('Target', self.df.columns)
        input_features = [c for c in self.df.columns if c != 'Target']
        self.assertEqual(len(input_features), 36)

    def test_nationality_spelling(self):
        """Ensure 'Nacionality' is corrected to 'Nationality'."""
        self.assertIn('Nationality', self.df.columns)
        self.assertNotIn('Nacionality', self.df.columns)

    def test_no_whitespace_or_bom_in_column_names(self):
        """Ensure no unnecessary leading/trailing whitespace, tabs, or BOM in column names."""
        self.assertFalse(self.raw_header.startswith('\ufeff'), "BOM should not be present in raw header")
        for col in self.df.columns:
            self.assertEqual(col, col.strip(), f"Column '{col}' contains leading or trailing whitespace")
            self.assertNotIn('\t', col, f"Column '{col}' contains tab character")
            self.assertNotIn('\ufeff', col, f"Column '{col}' contains BOM character")
            self.assertNotIn('"', col, f"Column '{col}' contains unexpected quotation marks")

    def test_daytime_evening_attendance_naming(self):
        """Verify Daytime/evening attendance has no trailing tab character."""
        self.assertIn('Daytime/evening attendance', self.df.columns)
        self.assertNotIn('Daytime/evening attendance\t', self.df.columns)

    # 2. Data Types
    def test_numerical_data_types(self):
        """Ensure numerical columns contain valid float or int values."""
        float_cols = [
            'Previous qualification (grade)', 'Admission grade',
            'Curricular units 1st sem (grade)', 'Curricular units 2nd sem (grade)',
            'Unemployment rate', 'Inflation rate', 'GDP'
        ]
        for col in float_cols:
            self.assertTrue(
                np.issubdtype(self.df[col].dtype, np.floating),
                f"Column '{col}' should be floating point type, found {self.df[col].dtype}"
            )

        int_cols = [
            'Marital status', 'Application mode', 'Application order', 'Course',
            'Daytime/evening attendance', 'Previous qualification', 'Nationality',
            "Mother's qualification", "Father's qualification", "Mother's occupation",
            "Father's occupation", 'Displaced', 'Educational special needs', 'Debtor',
            'Tuition fees up to date', 'Gender', 'Scholarship holder', 'Age at enrollment',
            'International', 'Curricular units 1st sem (credited)', 'Curricular units 1st sem (enrolled)',
            'Curricular units 1st sem (evaluations)', 'Curricular units 1st sem (approved)',
            'Curricular units 1st sem (without evaluations)', 'Curricular units 2nd sem (credited)',
            'Curricular units 2nd sem (enrolled)', 'Curricular units 2nd sem (evaluations)',
            'Curricular units 2nd sem (approved)', 'Curricular units 2nd sem (without evaluations)'
        ]
        for col in int_cols:
            self.assertTrue(
                np.issubdtype(self.df[col].dtype, np.integer),
                f"Column '{col}' should be integer type, found {self.df[col].dtype}"
            )

    def test_binary_columns_representation(self):
        """Ensure binary columns contain strictly 0 and 1."""
        binary_cols = [
            'Daytime/evening attendance', 'Displaced', 'Educational special needs',
            'Debtor', 'Tuition fees up to date', 'Gender', 'Scholarship holder', 'International'
        ]
        for col in binary_cols:
            unique_vals = set(self.df[col].unique())
            self.assertTrue(unique_vals.issubset({0, 1}), f"Column '{col}' contains non-binary values: {unique_vals}")

    # 3. Missing and Invalid Values
    def test_no_missing_or_null_values(self):
        """Ensure 0 nulls, NaNs, or missing values across all columns."""
        null_counts = self.df.isnull().sum()
        self.assertEqual(null_counts.sum(), 0, f"Found missing values:\n{null_counts[null_counts > 0]}")

    def test_no_blank_strings(self):
        """Ensure no blank or empty string values in any cell."""
        for col in self.df.columns:
            if self.df[col].dtype == object or self.df[col].dtype == 'string':
                empty_count = (self.df[col].astype(str).str.strip() == '').sum()
                self.assertEqual(empty_count, 0, f"Column '{col}' contains {empty_count} blank strings")

    # 4. Duplicate Records
    def test_no_duplicate_records(self):
        """Ensure dataset contains no exact duplicate rows."""
        dup_count = self.df.duplicated().sum()
        self.assertEqual(dup_count, 0, f"Found {dup_count} exact duplicate rows")

    # 5. Target Column
    def test_target_values_and_labels(self):
        """Verify that Target contains only: Graduate, Dropout, Enrolled."""
        expected_classes = {'Graduate', 'Dropout', 'Enrolled'}
        actual_classes = set(self.df['Target'].unique())
        self.assertEqual(actual_classes, expected_classes)
        self.assertEqual(len(self.df[self.df['Target'] == 'Graduate']), 2209)
        self.assertEqual(len(self.df[self.df['Target'] == 'Dropout']), 1421)
        self.assertEqual(len(self.df[self.df['Target'] == 'Enrolled']), 794)

    # 6. Numerical Anomalies
    def test_no_infinite_values(self):
        """Ensure no infinite values exist in numerical columns."""
        numeric_df = self.df.select_dtypes(include=[np.number])
        inf_count = np.isinf(numeric_df).sum().sum()
        self.assertEqual(inf_count, 0, f"Found {inf_count} infinite values")

    def test_numerical_ranges(self):
        """Verify values lie within legitimate domain bounds."""
        # Age
        self.assertGreaterEqual(self.df['Age at enrollment'].min(), 17)
        self.assertLessEqual(self.df['Age at enrollment'].max(), 100)
        
        # Grades
        self.assertGreaterEqual(self.df['Admission grade'].min(), 95.0)
        self.assertLessEqual(self.df['Admission grade'].max(), 200.0)
        self.assertGreaterEqual(self.df['Previous qualification (grade)'].min(), 95.0)
        self.assertLessEqual(self.df['Previous qualification (grade)'].max(), 200.0)
        self.assertGreaterEqual(self.df['Curricular units 1st sem (grade)'].min(), 0.0)
        self.assertLessEqual(self.df['Curricular units 1st sem (grade)'].max(), 20.0)
        self.assertGreaterEqual(self.df['Curricular units 2nd sem (grade)'].min(), 0.0)
        self.assertLessEqual(self.df['Curricular units 2nd sem (grade)'].max(), 20.0)

        # Macroeconomic ranges (defending negative inflation/GDP as legitimate Portuguese economic events)
        self.assertGreaterEqual(self.df['Unemployment rate'].min(), 0.0)
        self.assertGreaterEqual(self.df['Inflation rate'].min(), -5.0)
        self.assertLessEqual(self.df['Inflation rate'].max(), 10.0)
        self.assertGreaterEqual(self.df['GDP'].min(), -10.0)
        self.assertLessEqual(self.df['GDP'].max(), 10.0)

    def test_curricular_units_consistency(self):
        """Ensure approved units do not exceed enrolled units."""
        sem1_inv = (self.df['Curricular units 1st sem (approved)'] > self.df['Curricular units 1st sem (enrolled)']).sum()
        sem2_inv = (self.df['Curricular units 2nd sem (approved)'] > self.df['Curricular units 2nd sem (enrolled)']).sum()
        self.assertEqual(sem1_inv, 0, f"Sem 1 approved > enrolled in {sem1_inv} rows")
        self.assertEqual(sem2_inv, 0, f"Sem 2 approved > enrolled in {sem2_inv} rows")

    # 7. Data Integrity
    def test_record_count_and_structure(self):
        """Ensure all 4,424 student records are preserved with exact shape."""
        self.assertEqual(self.df.shape, (4424, 37))

if __name__ == '__main__':
    unittest.main()
