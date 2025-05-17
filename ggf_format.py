#!/usr/bin/env python

import numpy as np
from struct import unpack

class GGF:
    """
    A class to parse Trimble GGF (Grid File) binary files.

    This class reads a GGF file, validates its header, parses grid data,
    and provides access to various properties of the grid, such as boundaries,
    grid size, intervals, and the grid data itself.
    """

    # Define the fixed length of the GGF grid header
    GRID_HEADER_LENGTH = 146

    # Define common error codes for clarity
    ERROR_FILE_NOT_FOUND = 99
    ERROR_FILE_READ = 100
    ERROR_FILE_TOO_SMALL = 1
    ERROR_INVALID_SIGNATURE = 2
    ERROR_UNSUPPORTED_VERSION = 3
    ERROR_LAT_INCONSISTENCY = 4
    ERROR_LON_INCONSISTENCY = 5
    ERROR_FILE_SIZE_INCONSISTENCY = 6
    ERROR_UNITS_NOT_SET = 101
    ERROR_INTERPOLATION_NOT_SET = 102
    ERROR_DATA_FORMAT_NOT_SET = 103
    ERROR_LAT_DIRECTION_NOT_SET = 104
    ERROR_LON_DIRECTION_NOT_SET = 105
    ERROR_UNSUPPORTED_DATA_FORMAT = 202

    def __init__(self, file_path: str, strict: bool = True):
        """
        Initializes the GGF parser by reading and validating the file.

        Args:
            file_path (str): The path to the GGF binary file.
            strict (bool): If True, parsing will fail on non-critical
                           header inconsistencies (e.g., missing units/direction).
                           Defaults to True.
        """
        # Initialize all internal attributes to a default state
        self._valid: bool = False
        self._error_number: int = 0
        self._error_string: str = ""
        self._version: int | None = None
        self._name: str = ""
        self._lat_min: float = 0.0
        self._lat_max: float = 0.0
        self._long_min: float = 0.0
        self._long_max: float = 0.0
        self._lat_interval: float = 0.0
        self._long_interval: float = 0.0
        self._lat_grid_size: int = 0
        self._long_grid_size: int = 0
        self._grid_n_pole: float = 0.0
        self._grid_s_pole: float = 0.0
        self._grid_missing_value: float = 0.0
        self._grid_scalar: float = 0.0
        self._grid_window: int = 0
        self._flags: dict = {}
        self._grid: list | None = None
        self._min_value: float | None = None
        self._max_value: float | None = None
        self._min_value_footer: float | None = None
        self._max_value_footer: float | None = None
        self._missing_count: int = 0

        try:
            with open(file_path, 'rb') as file:
                ggf_file_data = file.read()
        except FileNotFoundError:
            self._set_error(self.ERROR_FILE_NOT_FOUND, f"File not found: {file_path}")
            return
        except Exception as e:
            self._set_error(self.ERROR_FILE_READ, f"Error reading file: {e}")
            return

        # Validate and parse the file data
        self._valid, self._error_number, self._error_string = self._validate_and_parse(
            ggf_file_data, strict
        )

    def _set_error(self, error_number: int, error_string: str):
        """Helper method to set error state."""
        self._valid = False
        self._error_number = error_number
        self._error_string = error_string

    # --- Public Properties to access parsed data ---

    @property
    def error_number(self) -> int:
        """Returns the error code if parsing failed, otherwise 0."""
        return self._error_number

    @property
    def error_string(self) -> str:
        """Returns the error message if parsing failed, otherwise an empty string."""
        return self._error_string

    @property
    def flags(self) -> dict:
        """Returns a dictionary of parsed header flags."""
        return self._flags

    @property
    def grid(self) -> list | None:
        """
        Returns the grid data as a flattened list.
        Missing values are represented as None.
        """
        return self._grid

    @property
    def lat_interval(self) -> float:
        """Returns the latitude interval between grid points."""
        return self._lat_interval

    @property
    def lat_grid_size(self) -> int:
        """Returns the number of grid points along the latitude axis (rows)."""
        return self._lat_grid_size

    @property
    def lat_min(self) -> float:
        """Returns the minimum latitude of the grid boundary."""
        return self._lat_min

    @property
    def lat_max(self) -> float:
        """Returns the maximum latitude of the grid boundary."""
        return self._lat_max

    @property
    def long_interval(self) -> float:
        """Returns the longitude interval between grid points."""
        return self._long_interval

    @property
    def long_grid_size(self) -> int:
        """Returns the number of grid points along the longitude axis (columns)."""
        return self._long_grid_size

    @property
    def long_min(self) -> float:
        """Returns the minimum longitude of the grid boundary."""
        return self._long_min

    @property
    def long_max(self) -> float:
        """Returns the maximum longitude of the grid boundary."""
        return self._long_max

    @property
    def grid_missing_value(self) -> float:
        """Returns the raw value used in the file to denote missing data."""
        return self._grid_missing_value

    @property
    def grid_n_pole(self) -> float:
        """Returns the value for the North Pole (if applicable)."""
        return self._grid_n_pole

    @property
    def grid_scalar(self) -> float:
        """Returns the scalar value used for scaled grid data."""
        return self._grid_scalar

    @property
    def grid_s_pole(self) -> float:
        """Returns the value for the South Pole (if applicable)."""
        return self._grid_s_pole

    @property
    def grid_window(self) -> int:
        """Returns the grid window value from the header."""
        return self._grid_window

    @property
    def min_value(self) -> float | None:
        """Returns the minimum value found in the grid data (excluding missing values)."""
        return self._min_value

    @property
    def min_value_footer(self) -> float | None:
        """Returns the minimum value found in the file footer (if version 1)."""
        return self._min_value_footer

    @property
    def max_value(self) -> float | None:
        """Returns the maximum value found in the grid data (excluding missing values)."""
        return self._max_value

    @property
    def max_value_footer(self) -> float | None:
        """Returns the maximum value found in the file footer (if version 1)."""
        return self._max_value_footer

    @property
    def rows(self) -> int:
        """Alias for LatGridSize."""
        return self._lat_grid_size

    @property
    def columns(self) -> int:
        """Alias for LongGridSize."""
        return self._long_grid_size

    @property
    def boundary_south(self) -> float:
        """Alias for LatMin."""
        return self._lat_min

    @property
    def boundary_north(self) -> float:
        """Alias for LatMax."""
        return self._lat_max

    @property
    def boundary_east(self) -> float:
        """Alias for LongMax."""
        return self._long_max

    @property
    def boundary_west(self) -> float:
        """Alias for LongMin."""
        return self._long_min

    @property
    def missing_count(self) -> int:
        """Returns the count of missing values in the grid."""
        return self._missing_count

    @property
    def valid(self) -> bool:
        """Returns True if the file was successfully parsed and validated, False otherwise."""
        return self._valid

    @property
    def version(self) -> int | None:
        """Returns the GGF file version."""
        return self._version

    # --- Internal Helper Methods ---

    def _bit_is_set(self, byte_val: int, bit_pos: int) -> bool:
        """
        Checks if a specific bit is set in a byte.

        Args:
            byte_val (int): The byte value (as an integer).
            bit_pos (int): The bit position (0-7).

        Returns:
            bool: True if the bit is set, False otherwise.
        """
        return ((byte_val >> bit_pos) & 1) != 0

    def _parse_flags(self, flags_bytes: bytes, strict: bool) -> tuple[bool, int, str]:
        """
        Parses the 8 bytes of flag data from the header.

        Args:
            flags_bytes (bytes): The 8 bytes containing the flag information.
            strict (bool): If True, enforces stricter validation of flags.

        Returns:
            tuple: (valid (bool), error_number (int), error_string (str))
        """
        flags = {}

        # Parse the first byte of flags (General Grid Information)
        flags["GIF_GRID_WRAPS"] = self._bit_is_set(flags_bytes[0], 0)
        flags["GIF_GRID_SCALED"] = self._bit_is_set(flags_bytes[0], 1)
        flags["GIF_GRID_CHECK_MISSING"] = self._bit_is_set(flags_bytes[0], 2)
        flags["GIF_GRID_NPOLE"] = self._bit_is_set(flags_bytes[0], 3)
        flags["GIF_GRID_SPOLE"] = self._bit_is_set(flags_bytes[0], 4)
        flags["GIF_GRID_XY"] = self._bit_is_set(flags_bytes[0], 5)
        flags["GIF_REVERSE_AXES"] = self._bit_is_set(flags_bytes[0], 6)
        flags["GIF_WGS84_BASED"] = self._bit_is_set(flags_bytes[0], 7)

        # Parse the second byte (Units)
        units_byte = flags_bytes[1]
        flags["GIF_UNITS_MILLIMETERS"] = self._bit_is_set(units_byte, 0)
        flags["GIF_UNITS_CENTIMETERS"] = self._bit_is_set(units_byte, 1)
        flags["GIF_UNITS_METERS"] = self._bit_is_set(units_byte, 2)
        flags["GIF_UNITS_SURVEY_INCHES"] = self._bit_is_set(units_byte, 3)
        flags["GIF_UNITS_SURVEY_FEET"] = self._bit_is_set(units_byte, 4)
        flags["GIF_UNITS_INTL_INCHES"] = self._bit_is_set(units_byte, 5)
        flags["GIF_UNITS_INTL_FEET"] = self._bit_is_set(units_byte, 6)

        # Validate Units flag
        if units_byte == 0:
            if strict:
                return False, self.ERROR_UNITS_NOT_SET, "Units not set in header flags"
            else:
                # Default to meters if not strictly enforced
                flags["GIF_UNITS_METERS"] = True

        # Parse the third byte (Interpolation)
        interp_byte = flags_bytes[2]
        if interp_byte == 0:
            return False, self.ERROR_INTERPOLATION_NOT_SET, "Interpolation method not set in header flags"

        flags["GIF_INTERP_LINEAR"] = self._bit_is_set(interp_byte, 0)
        flags["GIF_INTERP_BILINEAR"] = self._bit_is_set(interp_byte, 1)
        flags["GIF_INTERP_SPLINE"] = self._bit_is_set(interp_byte, 2)
        flags["GIF_INTERP_BIQUADRATIC"] = self._bit_is_set(interp_byte, 3)
        flags["GIF_INTERP_QUADRATIC"] = self._bit_is_set(interp_byte, 4)
        flags["GIF_INTERP_GPS_MSL"] = self._bit_is_set(interp_byte, 5)

        # Parse the fourth byte (Data Format)
        data_format_byte = flags_bytes[3]
        if data_format_byte == 0:
            return False, self.ERROR_DATA_FORMAT_NOT_SET, "Data format not set in header flags"

        flags["GIF_FORMAT_BYTE"] = self._bit_is_set(data_format_byte, 0)
        flags["GIF_FORMAT_SHORT"] = self._bit_is_set(data_format_byte, 1)
        flags["GIF_FORMAT_LONG"] = self._bit_is_set(data_format_byte, 2)
        flags["GIF_FORMAT_FLOAT"] = self._bit_is_set(data_format_byte, 3)
        flags["GIF_FORMAT_DOUBLE"] = self._bit_is_set(data_format_byte, 4)
        flags["GIF_FORMAT_LONG_DOUBLE"] = self._bit_is_set(data_format_byte, 5)

        # Check for supported data formats
        if not (flags["GIF_FORMAT_FLOAT"] or flags["GIF_FORMAT_LONG"]):
            return False, self.ERROR_UNSUPPORTED_DATA_FORMAT, "Only Long (32-bit integer) and Float (32-bit float) data formats are supported."

        # Parse the fifth byte (Latitude Direction)
        lat_dir_byte = flags_bytes[4]
        flags["GIF_LAT_ASCENDING"] = self._bit_is_set(lat_dir_byte, 0)
        flags["GIF_LAT_DESCENDING"] = self._bit_is_set(lat_dir_byte, 1)

        # Validate Latitude Direction flag
        if lat_dir_byte == 0:
            if strict:
                return False, self.ERROR_LAT_DIRECTION_NOT_SET, "Latitude direction not set in header flags"
            else:
                flags["GIF_LAT_ASCENDING"] = True

        # Parse the sixth byte (Longitude Direction)
        lon_dir_byte = flags_bytes[5]
        flags["GIF_LON_ASCENDING"] = self._bit_is_set(lon_dir_byte, 0)
        flags["GIF_LON_DESCENDING"] = self._bit_is_set(lon_dir_byte, 1)

        # Validate Longitude Direction flag
        if lon_dir_byte == 0:
            if strict:
                return False, self.ERROR_LON_DIRECTION_NOT_SET, "Longitude direction not set in header flags"
            else:
                flags["GIF_LON_ASCENDING"] = True

        # Bytes 7 and 8 are reserved and not currently parsed
        self._flags = flags
        return True, 0, ""

    def _parse_grid(self, ggf_file_bytes: bytes):
        """
        Parses the grid data from the file bytes.
        """
        self._grid = []
        self._min_value = None
        self._max_value = None
        self._missing_count = 0

        # Determine the base data format character and its byte size
        if self._flags["GIF_FORMAT_FLOAT"]:
            base_format_char = "f"  # 32-bit float
            data_byte_size = 4
        elif self._flags["GIF_FORMAT_LONG"]:
            base_format_char = "l"  # 32-bit signed integer
            data_byte_size = 4
        else:
            # This should ideally not happen if _parse_flags worked correctly
            # but as a fallback, raise an error for unsupported format.
            raise ValueError("Unsupported data format for grid parsing in _parse_grid.")

        # Construct the full unpack format string for a row.
        # The endianness specifier '<' must come first, then the count, then the type.
        # Example: "<100f" for 100 little-endian floats.
        row_unpack_format = f"<{self._long_grid_size}{base_format_char}"

        # Iterate through each latitude row
        for lat_idx in range(self._lat_grid_size):
            start_byte = self.GRID_HEADER_LENGTH + lat_idx * self._long_grid_size * data_byte_size
            end_byte = start_byte + self._long_grid_size * data_byte_size

            # Ensure there's enough data to unpack the current row
            if end_byte > len(ggf_file_bytes):
                raise IOError(f"File ended unexpectedly. Not enough data for grid row {lat_idx}. "
                              f"Expected {end_byte} bytes, found {len(ggf_file_bytes)}.")

            # Unpack the data for the current row
            try:
                row_raw_data = unpack(row_unpack_format, ggf_file_bytes[start_byte:end_byte])
            except StructError as e:
                # Provide more context if a struct.error occurs during unpacking
                raise IOError(f"Error unpacking grid data at row {lat_idx} (bytes {start_byte}-{end_byte}). "
                              f"Format: '{row_unpack_format}'. Error: {e}") from e

            # Process each data point in the row
            processed_row_data = []
            for value in row_raw_data:
                # Apply scalar if data is scaled
                if self._flags["GIF_GRID_SCALED"]:
                    # Avoid division by zero if scalar is somehow zero (unlikely for valid GGF)
                    if self._grid_scalar == 0.0:
                        processed_row_data.append(None) # Or handle as an error if appropriate
                        continue
                    value /= self._grid_scalar

                # Check for missing value marker
                if value == self._grid_missing_value:
                    processed_row_data.append(None)
                    self._missing_count += 1
                else:
                    processed_row_data.append(value)
                    # Update min/max values
                    if self._min_value is None or value < self._min_value:
                        self._min_value = value
                    if self._max_value is None or value > self._max_value:
                        self._max_value = value
            self._grid.extend(processed_row_data)

    def _validate_and_parse(self, ggf_file_bytes: bytes, strict: bool) -> tuple[bool, int, str]:
        """
        Validates the header and parses the main components of the GGF file.

        Args:
            ggf_file_bytes (bytes): The full bytes of the GGF file.
            strict (bool): If True, enforces stricter validation.

        Returns:
            tuple: (valid (bool), error_number (int), error_string (str))
        """
        # Check if the file is large enough to contain the header
        if len(ggf_file_bytes) < self.GRID_HEADER_LENGTH:
            return False, self.ERROR_FILE_TOO_SMALL, "File size is too small to contain the full header"

        # Check for the Trimble header signature
        if ggf_file_bytes[2:16] != b'TNL GRID FILE\x00':
            return False, self.ERROR_INVALID_SIGNATURE, "Missing the expected Trimble Header signature"

        # Unpack the file version (2-byte unsigned short, little-endian)
        self._version = unpack("<H", ggf_file_bytes[0:2])[0]
        if self._version > 1:
            return False, self.ERROR_UNSUPPORTED_VERSION, f"Unsupported GGF version: {self._version}. Only versions 0 and 1 are supported."

        # Unpack and decode the grid name (32-byte ASCII string, null-padded)
        self._name = unpack("32s", ggf_file_bytes[16:48])[0].decode('ascii').rstrip("\x00").rstrip()

        # Unpack boundary coordinates (8-byte doubles, little-endian)
        self._lat_min = unpack("<d", ggf_file_bytes[48:56])[0]
        self._lat_max = unpack("<d", ggf_file_bytes[56:64])[0]
        self._long_min = unpack("<d", ggf_file_bytes[64:72])[0]
        self._long_max = unpack("<d", ggf_file_bytes[72:80])[0]

        # Unpack interval sizes (8-byte doubles, little-endian)
        self._lat_interval = unpack("<d", ggf_file_bytes[80:88])[0]
        self._long_interval = unpack("<d", ggf_file_bytes[88:96])[0]

        # Unpack grid dimensions (4-byte unsigned integers, little-endian)
        self._lat_grid_size = unpack("<I", ggf_file_bytes[96:100])[0]
        self._long_grid_size = unpack("<I", ggf_file_bytes[100:104])[0]

        # Validate grid dimensions against boundary and interval values
        # Allow for a small floating-point tolerance (epsilon)
        EPSILON = 1e-4 # A common tolerance for geospatial data

        if abs((self._lat_min + (self._lat_grid_size - 1) * self._lat_interval) - self._lat_max) > EPSILON:
            return False, self.ERROR_LAT_INCONSISTENCY, "Latitude grid size and interval are inconsistent with Min/Max latitude values"

        if abs((self._long_min + (self._long_grid_size - 1) * self._long_interval) - self._long_max) > EPSILON:
            return False, self.ERROR_LON_INCONSISTENCY, "Longitude grid size and interval are inconsistent with Min/Max longitude values"

        # Unpack pole values, missing value marker, and scalar (8-byte doubles, little-endian)
        self._grid_n_pole = unpack("<d", ggf_file_bytes[104:112])[0]
        self._grid_s_pole = unpack("<d", ggf_file_bytes[112:120])[0]
        self._grid_missing_value = unpack("<d", ggf_file_bytes[120:128])[0]
        self._grid_scalar = unpack("<d", ggf_file_bytes[128:136])[0]

        # Unpack grid window (2-byte unsigned short, little-endian)
        self._grid_window = unpack("<H", ggf_file_bytes[136:138])[0]

        # Parse the flag bytes
        valid_flags, err_num_flags, err_string_flags = self._parse_flags(ggf_file_bytes[138:146], strict)
        if not valid_flags:
            return valid_flags, err_num_flags, err_string_flags

        # Calculate the expected size of the grid data in bytes
        # Assumes data format is either Long or Float (4 bytes each)
        grid_data_size_bytes = self._lat_grid_size * self._long_grid_size * 4

        # Validate total file size based on version
        expected_total_size = self.GRID_HEADER_LENGTH + grid_data_size_bytes
        if self._version == 1:
            expected_total_size += 16 # Version 1 has a 16-byte footer

        if len(ggf_file_bytes) != expected_total_size:
            return False, self.ERROR_FILE_SIZE_INCONSISTENCY, f"File size ({len(ggf_file_bytes)} bytes) is inconsistent with the calculated grid size ({grid_data_size_bytes} bytes) and header/footer for Version {self._version}"

        if self._version == 1:
            # Unpack footer min/max values
            footer_start = self.GRID_HEADER_LENGTH + grid_data_size_bytes
            self._min_value_footer = unpack("<d", ggf_file_bytes[footer_start : footer_start + 8])[0]
            self._max_value_footer = unpack("<d", ggf_file_bytes[footer_start + 8 : footer_start + 16])[0]

        # Parse the actual grid data
        self._parse_grid(ggf_file_bytes)

        return True, 0, "" # Return success

    def dump_undulations(self) -> np.ndarray:
        """
        Returns the grid data as a flattened numpy array.
        Missing values (None) are converted to NaN (Not a Number).
        """
        if self._grid is None:
            return np.array([]) # Return empty array if grid not parsed

        # Convert the list grid to a numpy array, handling None values
        # Use float type to accommodate NaN for missing values
        undulations_grid = np.array(self._grid, dtype=float)

        return undulations_grid
