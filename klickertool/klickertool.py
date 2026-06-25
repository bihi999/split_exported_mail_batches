import pandas as pd
import os
import tkinter as tk
from pandastable import Table, TableModel
from tkinter import messagebox


class ExcelFile:
    def __init__(self, filename):
        self.filename = filename
        self.xls = pd.ExcelFile(self.filename)
        self.data = self.read_data()

    def read_data(self):
        """
        Reads the data from the Excel file.

        If the sheet name 'Daten' exists, it reads the data from that sheet.
        If the sheet name 'Sheet1' exists, it reads the data from that sheet.
        Raises a ValueError if no valid sheet is found in the Excel file.

        Returns:
            DataFrame: The data read from the Excel file.
        """
        if "Daten" in self.xls.sheet_names:
            data = pd.read_excel(self.filename, sheet_name="Daten")
        elif "Sheet1" in self.xls.sheet_names:
            data = pd.read_excel(self.filename, sheet_name="Sheet1")
        else:
            raise ValueError("No valid sheet found in Excel file.")
        return data

    def get_data(self):
        """
        Returns the data read from the Excel file.

        Returns:
            DataFrame: The data read from the Excel file.
        """
        return self.data

    def get_all_sheets(self):
        """
        Reads all sheets from the Excel file and returns them as a dictionary of dataframes.

        Returns:
            dict: A dictionary with sheet names as keys and corresponding dataframes as values.
        """
        return {sheet: pd.read_excel(self.xls, sheet_name=sheet) for sheet in self.xls.sheet_names}


class DataHandler:
    def __init__(self, filename):
        """
        Initializes the DataHandler object.

        Args:
            filename (str): The name of the Excel file to be processed.
        """
        self.filename = filename
        self.excel_file = ExcelFile(filename)
        self.data = self.excel_file.get_data()
        self.groups = self.data.groupby('Nr.')
        self.current_group = self.groups.__iter__()
        self.all_sheets = self.excel_file.get_all_sheets()

    def get_next_group(self):
        """
        Retrieves the next group that has not been marked as 'done'.

        Returns:
            tuple: A tuple containing the group name and group data. Returns (None, None) if no more groups are available.
        """
        for group_name, group_data in self.groups:
            if 'done' not in group_data['Status'].values:
                return group_name, group_data
        return None, None

    def save_selected_row(self, nr, row_idx):
        """
        Saves the selected row for a group to the 'results.xlsx' file.

        Args:
            nr (int): The group number.
            row_idx (int): The index of the selected row within the group.

        Notes:
            - If 'results.xlsx' does not exist, the row is saved with a header.
            - If 'results.xlsx' already exists, the row is appended to the existing data without a header.

        Returns:
            None
        """
        # Get the selected row from the group data
        row = self.data[self.data['Nr.'] == nr].iloc[[row_idx]]

        if 'results.xlsx' not in os.listdir():
            row.to_excel('results.xlsx', index=False)  # Save with header when the file does not exist
        else:
            # Read the existing data
            with pd.ExcelFile('results.xlsx') as reader:
                existing_data = pd.read_excel(reader, sheet_name='Sheet1')

            # Append the new row
            new_data = pd.concat([existing_data, row], ignore_index=True)

            # Write the data back to the Excel file
            with pd.ExcelWriter('results.xlsx', engine='openpyxl') as writer:
                new_data.to_excel(writer, index=False, sheet_name='Sheet1')

    def mark_group_as_done(self, nr):
        """
        Marks a group and its corresponding sheets as 'done'.

        Args:
            nr (int): The group number to be marked as 'done'.

        Returns:
            None
        """
        self.data.loc[self.data['Nr.'] == nr, 'Status'] = 'done'
        for sheet, data in self.all_sheets.items():
            if 'Nr.' in data.columns:
                data.loc[data['Nr.'] == nr, 'Status'] = 'done'

    def save_all_sheets(self):
        """
        Saves all sheets in the original Excel file, including the modified ones, to the same file.

        Returns:
            None
        """
        with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
            for sheet, data in self.all_sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)

    def is_file_processed(self):
        """
        Checks if the entire file has been processed.

        Returns:
            bool: True if the file is processed, False otherwise.
        """
        return 'done' not in self.data['Status']



class GUIHandler:
    def __init__(self, data_handler):
        self.data_handler = data_handler

        # Setting up the Tkinter Window
        self.root = tk.Tk()
        self.root.title('Excel Duplicate Row Selector')

        # Adding Stop and Resume buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.stop_button = tk.Button(self.button_frame, text="Stop", command=self.on_stop)
        self.stop_button.pack(side=tk.LEFT)

        self.resume_button = tk.Button(self.button_frame, text="Resume", command=self.on_resume)
        self.resume_button.pack(side=tk.LEFT)

        # Creating DataFrame table
        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize the table with the first group
        self.table = Table(self.table_frame, dataframe=pd.DataFrame())
        self.table.show()

        self.display_next_group()

    def display_group(self, group_data):
        # Keep only the columns that you want to display
        columns_to_display = ["Nr.", "vollstaendiger_name", "*Firmenname*", "*Position*", "*Land*"]
        group_data = group_data[columns_to_display]

        # Update the table with the new data
        self.table.updateModel(TableModel(group_data))
        self.table.redraw()

        # Binding the table to the selection event
        self.table.bind('<ButtonRelease-1>', self.on_row_select)

    def on_row_select(self, event):
        selected_row_idx = self.table.getSelectedRow()
        selected_nr = self.table.model.df.iloc[selected_row_idx]['Nr.']
        self.data_handler.save_selected_row(selected_nr, selected_row_idx)
        self.data_handler.mark_group_as_done(selected_nr)

        # Display the next group immediately
        self.display_next_group()

    def display_next_group(self):
        group_name, group_data = self.data_handler.get_next_group()
        if group_data is not None:
            self.display_group(group_data)
        else:
            messagebox.showinfo("Information", "File processed completely.")

    def on_stop(self):
        self.root.destroy()

    def on_resume(self):
        self.display_next_group()

    def run(self):
        self.root.mainloop()


class Application:
    def __init__(self, filename):
        self.data_handler = DataHandler(filename)
        self.gui_handler = GUIHandler(self.data_handler)

    def run(self):
        self.gui_handler.run()
        self.data_handler.save_all_sheets()


if __name__ == "__main__":
    filename = 'C:\\Users\\bhildenbrandt\\OneDrive - Quadriga Hochschule Berlin GmbH\\Desktop\\pre_leads_pr_updates_germany_doublets.xlsx'  # replace with your actual Excel file name
    app = Application(filename)
    app.run()

