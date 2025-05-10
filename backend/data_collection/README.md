# Data Collection Component

This component is responsible for collecting movie and TV show data from JustWatch using the Firecrawl API.

## Setup

1. Install the required dependencies:
```bash
pip install -r ../../requirements.txt
```

2. Set up your environment variables:
```bash
export FIRECRAWL_API_KEY='fc-b919bc12801046eda3f0f837e11ccb3e'
```

Or create a `.env` file in the project root:
```
FIRECRAWL_API_KEY=fc-b919bc12801046eda3f0f837e11ccb3e
```

## Usage

Run the scraper:
```bash
python justwatch_scraper.py
```

The script will:
1. Fetch new releases from JustWatch
2. Extract relevant metadata (title, content type, streaming platforms, etc.)
3. Save the data in both JSON and CSV formats in the `data/raw` directory

## Data Structure

The scraper collects the following information for each movie/TV show:
- Title
- Content Type (movie/TV show)
- Streaming Platforms
- Release Date
- Genres
- Rating
- Synopsis
- Cast (when available)
- Director (when available)
- Duration (when available)

## Output

Data is saved in two formats:
1. JSON: `data/raw/justwatch_data_YYYYMMDD_HHMMSS.json`
2. CSV: `data/raw/justwatch_data_YYYYMMDD_HHMMSS.csv`

The timestamp in the filename ensures we maintain historical data and can track changes over time.
