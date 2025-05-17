#!/usr/bin/env python

import sys
from struct import *
import json
import math
import numpy as np

# Commented out normalization functions from the original code
# def normalizeLat(Lat):
#     while Lat < -90:
#         Lat +=180
#
#     while Lat > 90:
#         Lat -=180
#     return (Lat)
#
# def normalizeLong(Long):
#     while Long < -180:
#         Long +=360
#
#     while Long > 180:
#         Long -=360
#     return (Long)

class GGF:
    """
    A class to parse Trimble GGF (Grid File) binary files.

    This class reads a GGF file, validates its header, parses grid data,
    and provides access to various properties of the grid, such as boundaries,
    grid size, intervals, and the grid data itself.
    """

    # Define the fixed length of the GGF grid header
    GRID_HEADER_LENGTH = 146

    def __init__(self, file_path, strict):
        """
        Initializes the GGF parser by reading and validating the file.

        Args:
            file_path (str): The path to the GGF binary file.
            strict (bool): If True, parsing will fail on non-critical
                           header inconsistencies (e.g., missing units/direction).
        """
        self._version = None
        # Open the file in binary read mode
        try:
            with open(file_path, 'rb') as file:
                ggf_file_data = file.read()
        except FileNotFoundError:
            self._valid = False
            self._errorNumber = 99
            self._errorString = f"File not found: {file_path}"
            return
        except Exception as e:
            self._valid = False
            self._errorNumber = 100
            self._errorString = f"Error reading file: {e}"
            return

        # Validate and parse the file data
        (self._valid, self._errorNumber, self._errorString) = self.validateAndParse(ggf_file_data, strict)

    # --- Properties to access parsed data ---

    @property
    def errorNumber(self):
        """Returns the error code if parsing failed, otherwise 0."""
        return self._errorNumber

    @property
    def errorString(self):
        """Returns the error message if parsing failed, otherwise an empty string."""
        return self._errorString

    @property
    def Flags(self):
        """Returns a dictionary of parsed header flags."""
        return self._flags

    @property
    def Grid(self):
        """
        Returns the grid data as a flattened list.
        Missing values are represented as None.
        """
        return self._grid

    # Note: Grid2D property is not implemented in the original code
    # @property
    # def Grid2D(self):
    #     """Returns the grid data as a 2D numpy array."""
    #     # This would require reshaping the self._grid list
    #     return self._grid2D # Placeholder

    @property
    def LatInterval(self):
        """Returns the latitude interval between grid points."""
        return self._LatInterval

    @property
    def LatGridSize(self):
        """Returns the number of grid points along the latitude axis (rows)."""
        return self._LatGridSize

    @property
    def LatMin(self):
        """Returns the minimum latitude of the grid boundary."""
        return self._LatMin

    @property
    def LatMax(self):
        """Returns the maximum latitude of the grid boundary."""
        return self._LatMax

    @property
    def LongInterval(self):
        """Returns the longitude interval between grid points."""
        return self._LongInterval

    @property
    def LongGridSize(self):
        """Returns the number of grid points along the longitude axis (columns)."""
        return self._LongGridSize

    @property
    def LongMin(self):
        """Returns the minimum longitude of the grid boundary."""
        return self._LongMin

    @property
    def LongMax(self):
        """Returns the maximum longitude of the grid boundary."""
        return self._LongMax

    @property
    def GridMissing(self):
        """Returns the raw value used in the file to denote missing data."""
        return self._GridMissing

    @property
    def GridNPole(self):
        """Returns the value for the North Pole (if applicable)."""
        return self._GridNPole

    @property
    def GridScalar(self):
        """Returns the scalar value used for scaled grid data."""
        return self._GridScalar

    @property
    def GridSPole(self):
        """Returns the value for the South Pole (if applicable)."""
        return self._GridSPole

    @property
    def GridWindow(self):
        """Returns the grid window value from the header."""
        return self._GridWindow

    @property
    def MinValue(self):
        """Returns the minimum value found in the grid data (excluding missing values)."""
        return self._MinValue

    @property
    def MinValueFooter(self):
        """Returns the minimum value found in the file footer (if version 1)."""
        return self._MinValueFooter

    @property
    def MaxValue(self):
        """Returns the maximum value found in the grid data (excluding missing values)."""
        return self._MaxValue

    @property
    def MaxValueFooter(self):
        """Returns the maximum value found in the file footer (if version 1)."""
        return self._MaxValueFooter

    @property
    def rows(self):
        """Alias for LatGridSize."""
        return self._LatGridSize

    @property
    def columns(self):
        """Alias for LongGridSize."""
        return self._LongGridSize

    @property
    def boundary_south(self):
        """Alias for LatMin."""
        return self._LatMin

    @property
    def boundary_north(self):
        """Alias for LatMax."""
        return self._LatMax

    @property
    def boundary_east(self):
        """Alias for LongMax."""
        return self._LongMax

    @property
    def boundary_west(self):
        """Alias for LongMin."""
        return self._LongMin

    @property
    def Missing(self):
        """Returns the count of missing values in the grid."""
        return self._Missing

    @property
    def valid(self):
        """Returns True if the file was successfully parsed and validated, False otherwise."""
        return self._valid

    @property
    def version(self):
        """Returns the GGF file version."""
        return self._version

    # --- Internal Helper Methods ---

    def bitSet(self, b, bit):
        """
        Checks if a specific bit is set in a byte.

        Args:
            b (int): The byte value (as an integer).
            bit (int): The bit position (0-7).

        Returns:
            bool: True if the bit is set, False otherwise.
        """
        # In Python 3, bytes read from a file are integers, so ord() is not needed
        testBit = 1 << bit
        return ((b & testBit) != 0)

    def parseFlags(self, flags_bytes, strict):
        """
        Parses the 8 bytes of flag data from the header.

        Args:
            flags_bytes (bytes): The 8 bytes containing the flag information.
            strict (bool): If True, enforces stricter validation of flags.

        Returns:
            tuple: (valid (bool), errorNumber (int), errorString (str))
        """
        self._flags = {}

        # Parse the first byte of flags
        self._flags["GIF_GRID_WRAPS"] = self.bitSet(flags_bytes[0], 0)
        self._flags["GIF_GRID_SCALED"] = self.bitSet(flags_bytes[0], 1)
        self._flags["GIF_GRID_CHECK_MISSING"] = self.bitSet(flags_bytes[0], 2)
        self._flags["GIF_GRID_NPOLE"] = self.bitSet(flags_bytes[0], 3)
        self._flags["GIF_GRID_SPOLE"] = self.bitSet(flags_bytes[0], 4)
        self._flags["GIF_GRID_XY"] = self.bitSet(flags_bytes[0], 5)
        self._flags["GIF_REVERSE_AXES"] = self.bitSet(flags_bytes[0], 6)
        self._flags["GIF_WGS84_BASED"] = self.bitSet(flags_bytes[0], 7)

        # Parse the second byte (Units)
        self._flags["GIF_UNITS_MILLIMETERS"] = self.bitSet(flags_bytes[1], 0)
        self._flags["GIF_UNITS_CENTIMETERS"] = self.bitSet(flags_bytes[1], 1)
        self._flags["GIF_UNITS_METERS"] = self.bitSet(flags_bytes[1], 2)
        self._flags["GIF_UNITS_SURVEY_INCHES"] = self.bitSet(flags_bytes[1], 3)
        self._flags["GIF_UNITS_SURVEY_FEET"] = self.bitSet(flags_bytes[1], 4)
        self._flags["GIF_UNITS_INTL_INCHES"] = self.bitSet(flags_bytes[1], 5)
        self._flags["GIF_UNITS_INTL_FEET"] = self.bitSet(flags_bytes[1], 6)

        # Validate Units flag
        if flags_bytes[1] == 0:
            if strict:
                return(False, 101, "Units not set in header flags")
            else:
                # Default to meters if not strictly enforced
                self._flags["GIF_UNITS_METERS"] = True

        # Parse the third byte (Interpolation)
        if flags_bytes[2] == 0:
             # Interpolation must be set
            return(False, 102, "Interpolation method not set in header flags")

        self._flags["GIF_INTERP_LINEAR"] = self.bitSet(flags_bytes[2], 0)
        self._flags["GIF_INTERP_BILINEAR"] = self.bitSet(flags_bytes[2], 1)
        self._flags["GIF_INTERP_SPLINE"] = self.bitSet(flags_bytes[2], 2)
        self._flags["GIF_INTERP_BIQUADRATIC"] = self.bitSet(flags_bytes[2], 3)
        self._flags["GIF_INTERP_QUADRATIC"] = self.bitSet(flags_bytes[2], 4)
        self._flags["GIF_INTERP_GPS_MSL"] = self.bitSet(flags_bytes[2], 5)

        # Parse the fourth byte (Data Format)
        if flags_bytes[3] == 0:
             # Data format must be set
            return(False, 103, "Data format not set in header flags")

        self._flags["GIF_FORMAT_BYTE"] = self.bitSet(flags_bytes[3], 0)
        self._flags["GIF_FORMAT_SHORT"] = self.bitSet(flags_bytes[3], 1)
        self._flags["GIF_FORMAT_LONG"] = self.bitSet(flags_bytes[3], 2)
        self._flags["GIF_FORMAT_FLOAT"] = self.bitSet(flags_bytes[3], 3)
        self._flags["GIF_FORMAT_DOUBLE"] = self.bitSet(flags_bytes[3], 4)
        self._flags["GIF_FORMAT_LONG_DOUBLE"] = self.bitSet(flags_bytes[3], 5)

        # Check for supported data formats
        if not (self._flags["GIF_FORMAT_FLOAT"] or self._flags["GIF_FORMAT_LONG"]):
            return(False, 202, "Only Long (32-bit integer) and Float (32-bit float) data formats are supported at this time")

        # Parse the fifth byte (Latitude Direction)
        self._flags["GIF_LAT_ASCENDING"] = self.bitSet(flags_bytes[4], 0)
        self._flags["GIF_LAT_DESCENDING"] = self.bitSet(flags_bytes[4], 1)

        # Validate Latitude Direction flag
        if flags_bytes[4] == 0:
            if strict:
                return(False, 104, "Latitude direction not set in header flags")
            else:
                # Default to ascending if not strictly enforced
                self._flags["GIF_LAT_ASCENDING"] = True

        # Parse the sixth byte (Longitude Direction)
        self._flags["GIF_LON_ASCENDING"] = self.bitSet(flags_bytes[5], 0)
        self._flags["GIF_LON_DESCENDING"] = self.bitSet(flags_bytes[5], 1)

        # Validate Longitude Direction flag
        if flags_bytes[5] == 0:
            if strict:
                return(False, 105, "Longitude direction not set in header flags")
            else:
                # Default to ascending if not strictly enforced
                self._flags["GIF_LON_ASCENDING"] = True

        # Bytes 7 and 8 are reserved and not currently parsed

        return(True, 0, "") # Return success

    def parseGrid(self, ggfFile_bytes, isFloat, isScaled, scalar):
        """
        Parses the grid data from the file bytes.

        Args:
            ggfFile_bytes (bytes): The full bytes of the GGF file.
            isFloat (bool): True if the data format is float, False if long.
            isScaled (bool): True if the data is scaled.
            scalar (float): The scalar value to apply if scaled.
        """
        self._grid = [] # Initialize grid as an empty list
        self._MinValue = None # Initialize min value
        self._MaxValue = None # Initialize max value
        self._Missing = 0 # Initialize missing value count

        # Determine the size of each data point in bytes
        data_size = 4 # Long and Float are both 4 bytes

        # Iterate through each latitude row
        for lat in range(self._LatGridSize):
            # Calculate the start and end byte indices for the current row
            start = self.GRID_HEADER_LENGTH + lat * self._LongGridSize * data_size
            end = self.GRID_HEADER_LENGTH + (lat + 1) * self._LongGridSize * data_size

            # Unpack the data for the current row
            if isFloat:
                # Unpack as 32-bit floats (little-endian)
                row_data = list(unpack("<{}f".format(self._LongGridSize), ggfFile_bytes[start: end]))
            else:
                # Unpack as 32-bit signed integers (little-endian)
                row_data = list(unpack("<{}l".format(self._LongGridSize), ggfFile_bytes[start: end]))

            # Apply scalar if data is scaled
            if isScaled:
                row_data = [x / scalar for x in row_data]

            # Process each data point in the row
            for data_index in range(len(row_data)):
                # Check for missing value marker
                if row_data[data_index] == self._GridMissing:
                    row_data[data_index] = None # Replace missing marker with None
                    self._Missing += 1 # Increment missing count
                else:
                    # Update min/max values if the data point is not missing
                    if self._MinValue is None or row_data[data_index] < self._MinValue:
                        self._MinValue = row_data[data_index]

                    if self._MaxValue is None or row_data[data_index] > self._MaxValue:
                        self._MaxValue = row_data[data_index]

            # Append the processed row data to the main grid list
            self._grid.extend(row_data)

    def validateAndParse(self, ggfFile_bytes, strict):
        """
        Validates the header and parses the main components of the GGF file.

        Args:
            ggfFile_bytes (bytes): The full bytes of the GGF file.
            strict (bool): If True, enforces stricter validation.

        Returns:
            tuple: (valid (bool), errorNumber (int), errorString (str))
        """
        # Check if the file is large enough to contain the header
        if len(ggfFile_bytes) < self.GRID_HEADER_LENGTH:
            return(False, 1, "File size is too small to contain the full header")

        # Check for the Trimble header signature
        if ggfFile_bytes[2:16] != b'TNL GRID FILE\x00':
            return(False, 2, "Missing the expected Trimble Header signature")

        # Unpack the file version (2-byte unsigned short, little-endian)
        version = unpack("<H", ggfFile_bytes[0:2])[0]
        if version > 1:
            # Only versions 0 and 1 are currently supported
            return(False, 3, f"Unsupported GGF version: {version}. Only versions 0 and 1 are supported.")
        self._version = version

        # Unpack and decode the grid name (32-byte ASCII string, null-padded)
        Name = unpack("32s", ggfFile_bytes[16:48])[0]
        Name = Name.decode('ascii')
        Name = Name.rstrip("\x00") # Remove null padding
        Name = Name.rstrip() # Remove trailing whitespace
        self._Name = Name

        # Unpack boundary coordinates (8-byte doubles, little-endian)
        self._LatMin = unpack("<d", ggfFile_bytes[48:56])[0]
        self._LatMax = unpack("<d", ggfFile_bytes[56:64])[0]
        self._LongMin = unpack("<d", ggfFile_bytes[64:72])[0]
        self._LongMax = unpack("<d", ggfFile_bytes[72:80])[0]

        # Unpack interval sizes (8-byte doubles, little-endian)
        self._LatInterval = unpack("<d", ggfFile_bytes[80:88])[0]
        self._LongInterval = unpack("<d", ggfFile_bytes[88:96])[0]

        # Unpack grid dimensions (4-byte unsigned integers, little-endian)
        self._LatGridSize = unpack("<I", ggfFile_bytes[96:100])[0]
        self._LongGridSize = unpack("<I", ggfFile_bytes[100:104])[0]

        # Validate grid dimensions against boundary and interval values
        # Allow for a small floating-point tolerance
        if abs((self._LatMin + (self._LatGridSize - 1) * self._LatInterval) - self._LatMax) > 0.0001:
            return(False, 4, "Latitude grid size and interval are inconsistent with Min/Max latitude values")

        if abs(self._LongMin + (self._LongGridSize - 1) * self._LongInterval - self._LongMax) > 0.0001:
            return(False, 5, "Longitude grid size and interval are inconsistent with Min/Max longitude values")

        # Unpack pole values, missing value marker, and scalar (8-byte doubles, little-endian)
        self._GridNPole = unpack("<d", ggfFile_bytes[104:112])[0]
        self._GridSPole = unpack("<d", ggfFile_bytes[112:120])[0]
        self._GridMissing = unpack("<d", ggfFile_bytes[120:128])[0]
        self._GridScalar = unpack("<d", ggfFile_bytes[128:136])[0]

        # Unpack grid window (2-byte unsigned short, little-endian)
        self._GridWindow = unpack("<H", ggfFile_bytes[136:138])[0]

        # Parse the flag bytes
        (valid, errNum, errString) = self.parseFlags(ggfFile_bytes[138:146], strict)
        if not valid:
            return (valid, errNum, errString) # Return flag parsing errors

        # Calculate the expected size of the grid data in bytes
        # Assuming data format is either Long or Float (4 bytes each)
        gridSize = (self._LatGridSize) * (self._LongGridSize) * 4

        # Validate total file size based on version
        if version == 0:
            # Version 0 has no footer
            if len(ggfFile_bytes) != gridSize + self.GRID_HEADER_LENGTH:
                return(False, 6, f"File size ({len(ggfFile_bytes)} bytes) is inconsistent with the calculated grid size ({gridSize} bytes) for Version 0")
            self._MinValueFooter = None # No footer min/max in V0
            self._MaxValueFooter = None
        elif version == 1:
            # Version 1 has a 16-byte footer (2 doubles for min/max)
            if len(ggfFile_bytes) != gridSize + self.GRID_HEADER_LENGTH + 16:
                return(False, 6, f"File size ({len(ggfFile_bytes)} bytes) is inconsistent with the calculated grid size ({gridSize} bytes) and footer for Version 1")
            # Unpack footer min/max values
            footer_start = gridSize + self.GRID_HEADER_LENGTH
            self._MinValueFooter = unpack("<d", ggfFile_bytes[footer_start : footer_start + 8])[0]
            self._MaxValueFooter = unpack("<d", ggfFile_bytes[footer_start + 8 : footer_start + 16])[0]

        # Parse the actual grid data
        self.parseGrid(ggfFile_bytes, self._flags["GIF_FORMAT_FLOAT"], self._flags["GIF_GRID_SCALED"], self.GridScalar)

        # Optional: Validate calculated min/max against footer min/max for Version 1
        # This check is commented out in the original, but could be added for stricter validation
        # if version == 1:
        #     if abs(self._MinValue - self._MinValueFooter) > 0.0001 or abs(self._MaxValue - self._MaxValueFooter) > 0.0001:
        #          # This might indicate an issue, depending on how min/max are calculated/stored
        #          print("Warning: Calculated min/max values differ from footer values.")


        return(True, 0, "") # Return success

    def dump_undulations(self):
        """
        Returns the grid data as a flattened numpy array.
        Missing values (None) are converted to NaN (Not a Number).
        """
        # Convert the list grid to a numpy array, handling None values
        # Use float type to accommodate NaN for missing values
        undulations_grid = np.array(self.Grid, dtype=float)

        # Reshape the flattened array into a 2D grid (rows x columns)
        # Note: The original code flattens it again after reshaping, which is redundant.
        # Returning the flattened array directly from self.Grid is simpler if that's the goal.
        # If a 2D array is desired, the reshape line is correct.
        # undulations_grid = undulations_grid.reshape((self.LatGridSize, self.LongGridSize))

        # The original code then flattens the reshaped array again.
        # This is equivalent to just returning the initial flattened numpy array.
        # undulations = undulations_grid.flatten()

        # Return the flattened numpy array directly
        return undulations_grid

# Example Usage (optional - uncomment to test)
# if __name__ == "__main__":
#     # Replace 'path/to/your/file.ggf' with the actual path to a GGF file
#     file_path = 'path/to/your/file.ggf'
#     strict_parsing = False # Set to True for stricter validation
#
#     ggf_data = GGF(file_path, strict_parsing)
#
#     if ggf_data.valid:
#         print("GGF file parsed successfully!")
#         print(f"Version: {ggf_data.version}")
#         print(f"Name: {ggf_data._Name}") # Accessing internal _Name property
#         print(f"Latitude Range: {ggf_data.LatMin} to {ggf_data.LatMax}")
#         print(f"Longitude Range: {ggf_data.LongMin} to {ggf_data.LongMax}")
#         print(f"Grid Size: {ggf_data.LatGridSize} rows x {ggf_data.LongGridSize} columns")
#         print(f"Latitude Interval: {ggf_data.LatInterval}")
#         print(f"Longitude Interval: {ggf_data.LongInterval}")
#         print(f"Min Value (calculated): {ggf_data.MinValue}")
#         print(f"Max Value (calculated): {ggf_data.MaxValue}")
#         if ggf_data.version == 1:
#              print(f"Min Value (footer): {ggf_data.MinValueFooter}")
#              print(f"Max Value (footer): {ggf_data.MaxValueFooter}")
#         print(f"Number of Missing Values: {ggf_data.Missing}")
#         print("\nFlags:")
#         for flag, value in ggf_data.Flags.items():
#             print(f"  {flag}: {value}")
#
#         # Get the grid data as a numpy array
#         undulations = ggf_data.dump_undulations()
#         print(f"\nGrid data (flattened numpy array, first 10 values): {undulations[:10]}")
#         print(f"Shape of flattened array: {undulations.shape}")
#
#         # If you need the 2D grid:
#         # undulations_2d = undulations.reshape((ggf_data.LatGridSize, ggf_data.LongGridSize))
#         # print(f"Shape of 2D array: {undulations_2d.shape}")
#
#     else:
#         print(f"Error parsing GGF file: [{ggf_data.errorNumber}] {ggf_data.errorString}")


