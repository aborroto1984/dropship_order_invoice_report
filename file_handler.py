import os


class FileHandler:

    def __init__(self, report_date):
        self.report_date = report_date

    DATE_FORMAT = "%m%d%Y"
    TIME_FORMAT = "%H%M%S"
    BASE_DIRECTORY = "tmp"

    def save_data_to_file(self, invoice_data_df, ftp_folder_name):
        """Saves the tracking data to a file."""
        if invoice_data_df.empty:
            return False
        directory_path = self._create_directory_structure(ftp_folder_name)
        date_str = self.report_date.strftime(FileHandler.DATE_FORMAT)
        file_path = f"{directory_path}\\Invoice_{date_str}.csv"

        try:
            invoice_data_df.to_csv(file_path, index=False)
            return file_path
        except Exception as e:
            print(f"Error while saving tracking data to file: {e}")
            raise

    def _create_directory_structure(self, ftp_folder_name):
        """Creates the directory structure for the tracking files."""
        datetime_str = self.report_date.strftime(
            f"{FileHandler.DATE_FORMAT}_{FileHandler.TIME_FORMAT}"
        )
        dir_path = os.path.join(
            FileHandler.BASE_DIRECTORY, ftp_folder_name, datetime_str
        )

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        return dir_path
