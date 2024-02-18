import ctypes
import os
from ctypes import wintypes
from ctypes import byref, sizeof


from PIL import Image
import ctypes
import atexit
import win32con
import win32gui
import os
import time
from win32con import IMAGE_CURSOR, LR_COPYFROMRESOURCE
from win32gui import GetIconInfo, GetClientRect
from ctypes import wintypes
from win32con import IMAGE_BITMAP

class MouseCursorManager:
    def __init__(self):
        self.cursor_history = []  # List to store cursor history

        self.custom_cursors=[]
        self.custom_cursor_path = os.path.abspath('crosshair.cur')

        self.populate_cursor_history()
        self.prev_condition = False




        print("Nathan Cursor Init")

    class CURSORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hCursor", ctypes.c_void_p),
            ("ptScreenPos", wintypes.POINT),
        ]

    def get_current_cursor(self):
        cursor_info = self.CURSORINFO()
        cursor_info.cbSize = ctypes.sizeof(self.CURSORINFO)

        if ctypes.windll.user32.GetCursorInfo(ctypes.byref(cursor_info)):
            return cursor_info.hCursor
        else:
            return None

    # Map known cursor IDs to their corresponding names
    hcursor_id_mapping = {
        65541: "IDC_IBEAM",
        65539: "IDC_ARROW",
        65567: "IDC_HAND"
        # Add more mappings as needed
    }

    def get_cursor_type(self, cursor):
        # Find the cursor ID in the history based on the cursor handle
        cursor_id = None

        for a, cursor_handle, b in self.cursor_history:

            if cursor_handle == cursor:
                cursor_id = a
                break

        if cursor_id is not None:
            print("Get Cursor Type Func", cursor_id)
            return cursor_id
        else:
            print("Cursor ID not found in history")
            return None

    def save_system_cursor(self, id_cursor):
        # Save the current system cursor before changing it
        cursor = ctypes.windll.user32.LoadImageW(0, id_cursor, win32con.IMAGE_CURSOR, 0, 0, win32con.LR_SHARED)
        saved_cursor = ctypes.windll.user32.CopyImage(cursor, win32con.IMAGE_CURSOR, 0, 0, win32con.LR_COPYFROMRESOURCE)
        return saved_cursor

    def populate_cursor_history(self):
        # Populate cursor history with common system cursors
        for cursor_id in range(32512, 32767):  # Cursor IDs typically range from 32640 to 32767
            cursor = ctypes.windll.user32.LoadCursorW(0, cursor_id)

            if cursor:
                self.custom_cursors.append(self.create_custom_cursor_handle(self.custom_cursor_path))
                cursor_himage = self.save_system_cursor(cursor_id)
                self.cursor_history.append((cursor_id, cursor, cursor_himage))

    def create_custom_cursor_handle(self,cursor_path, icon_size=(32,32)):
        # Load the custom cursor from a file
        l_custom_cursor = win32gui.LoadImage(0, cursor_path, win32con.IMAGE_CURSOR, *icon_size,  win32con.LR_LOADFROMFILE)

        return l_custom_cursor
    def change_mouse_pointer(self, condition):
        # Save the current cursor and condition
        # current_cursor = self.get_current_cursor()

        if self.prev_condition is None:
            print("Nathan Shold not be None")
            self.prev_condition = condition
            # self.original_cursor = current_cursor

        # Check if the condition has changed
        if condition != self.prev_condition:
            # Get the cursor type of the current cursor
            # current_cursor_type = self.get_cursor_type(current_cursor)

            # Set the custom cursor with the same type as the current cursor
            if condition:
                # print(f"Changing current cursor {current_cursor_type} custom cursor")
                print("Changing all cursors")
                for (cursor_id, hcursor_image_loc, saved_hcursor_image_loc), custom_cursor in zip(self.cursor_history, self.custom_cursors):
                    print(f"Changing cursor {cursor_id} to {custom_cursor}")
                    ctypes.windll.user32.SetSystemCursor(custom_cursor, cursor_id)

                # Originally ctypes.windll.user32.SetSystemCursor(self.custom_cursor, current_cursor_type)
            else:
                print("Resetting cursors")
                self.restore_original_cursor()

            # Update the previous condition
            self.prev_condition = condition

    def restore_original_cursor(self):
        for (cursor_id, hcursor_image_loc, saved_hcursor_image_loc), custom_cursor in zip(self.cursor_history, self.custom_cursors):
            print(f"Restoring cursor with ID: {cursor_id}, Type: {hcursor_image_loc}, Handle: {saved_hcursor_image_loc}")
            ctypes.windll.user32.SetSystemCursor(saved_hcursor_image_loc, cursor_id)
            ctypes.windll.user32.DestroyCursor(custom_cursor)

        self.cursor_history = []
        self.custom_cursors = []
        self.populate_cursor_history()
        self.prev_condition = False  # Reset the previous condition after restoration



def test_mouse_cursor_manager():
    # Create an instance of MouseCursorManager
    cursor_manager = MouseCursorManager()

    # Test changing the mouse pointer

    cursor_manager.change_mouse_pointer(True)  # Change to custom cursor
    input("Press Enter to continue...")  # Wait for user input
    cursor_manager.change_mouse_pointer(False)  # Reset to original cursor

    # Additional testing can be added based on your requirements

if __name__ == "__main__":
    test_mouse_cursor_manager()
