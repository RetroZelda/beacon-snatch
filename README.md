# Beacon Snatch

Beacon Snatch is a command-line interface (CLI) tool designed to authenticate, browse, and download video content from the Beacon streaming platform. The CLI offers both direct command execution and an interactive mode for ease of use.

It is also a python library for more advanced usage.

## Features

- **Authentication**: Authenticate with your Beacon account using email and password or saved cookies.
- **Series Management**: List available series, fetch series details, and download all content from a series.
- **Content Management**: Fetch content details, display available streams, and download specific content by ID.
- **Interactive Mode**: A user-friendly interactive command shell for managing your content downloads.
- **Output and Cache Management**: Set the directory where downloaded files are saved and manage cached cookies for session persistence.

## Installation

To install Beacon Snatch, first clone the repository and then install it using `pip`:

```bash
git clone https://github.com/retrozelda/beacon_snatch.git
cd beacon_snatch
pip install .
```
This will install the required dependencies listed in the dependencies file and make the CLI accessible via the `beacon-snatch` command.

## CLI Usage
You can run Beacon Snatch either in interactive mode or by directly executing commands.

Command-Line Mode
Run any of the following commands directly from the terminal:
```
# Authenticate with your Beacon account
beacon-snatch authenticate

# List all available series
beacon-snatch list-series

# Get detailed information about a specific series
beacon-snatch series-info <series_id>

# List content in a specific series
beacon-snatch series-list-content <series_id>

# Download all content from a specific series
beacon-snatch series-download <series_id>

# Get detailed information about specific content
beacon-snatch content-info <content_id>

# Download specific content by content ID
beacon-snatch content-download <content_id>

# Set the output directory where downloaded files will be saved
beacon-snatch set-output <output_dir>

# Clear the stored authentication cookies
beacon-snatch clear-cookies

# View configuration info for the current session
beacon-snatch info

# Exit the CLI
beacon-snatch exit
```

### Interactive Mode
Start the interactive mode for easier use:

```
beacon-snatch interactive
```
In interactive mode, you can type any of the above commands without the need to prefix them with beacon-snatch.

#### Example Interactive Session:
```
(Beacon) > authenticate
Enter your Beacon Email: your-email@example.com
Enter your Beacon Password:
Authenticated as: your-username

(Beacon) > list-series
0) series-1
1) series-2
2) series-3

(Beacon) > series-info series-1
	id:
		123
	title:
		Example Series Title
	description:
		This is an example series description.
	series_url:
		https://beacon.tv/series/series-1
	content count:
		10

(Beacon) > exit
Goodbye!
```
### Configuration Options
When starting the CLI, you can set the following options:

- **--log-level [DEBUG|VERBOSE|INFO|WARNING|ERROR|CRITICAL]**: Set the logging level.
- **--cache <cache_dir>**: Path to the cache directory. If not provided, a default will be used.
- **--output <output_dir>**: Path to save downloads. If not provided, a default will be used.

#### Example usage:
```
beacon-snatch --log-level INFO --cache ~/.beacon_cache --output ~/downloads authenticate
```

## Python Library Usage
You can also use Beacon Snatch as a Python library to integrate its functionality into your own applications. Here's an example of how to use the library:

### Example Usage
```
from beacon_snatch import BeaconAuthentication, BeaconSeries, BeaconContent

# Authenticate with your Beacon account
auth = BeaconAuthentication(email="your-email@example.com", password="your-password")
auth.authenticate()

# List available series
series_ids = BeaconSeries.get_all_series(auth)
print(series_ids)

# Get detailed information about a specific series
series = BeaconSeries.create(auth, "series_id")
print(f"Title: {series.title}")
print(f"Description: {series.description}")

# Fetch and list content in the series
series.fetch(auth)
for content in series.content:
    print(f"Content Title: {content.title}")

# Download a specific content
content = BeaconContent.create(auth, "content_id")
if content:
    stream = content.video_and_audio_streams[0]  # Selects the highest resolution stream
    content.download(stream, destination_folder="./downloads")
```

#### Available Classes
- **BeaconAuthentication**: Handles authentication and session management.
- **BeaconSeries**: Manages series data and content fetching.
- **BeaconContent**: Manages individual content items and downloading.
- **BeaconStreamInfo**: Represents available streams for a content item (e.g., video, audio, etc).

# Dependencies
The project relies on several Python libraries, including:

- selenium
- requests
- progressbar2
- m3u8
- click

These are automatically installed when you install the project using pip.

# License
This project is licensed under the MIT License.
