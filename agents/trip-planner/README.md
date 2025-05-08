# Travel Advisor App

A Streamlit application that creates personalized travel plans and visual tours for any destination using Toolhouse.ai agents.

![Travel Advisor App Screenshot](assets/demo.gif)

## What This App Does

The Travel Advisor app helps you plan your next trip by:

1. **Creating personalized travel plans** based on your destination, age, and trip duration
2. **Generating visual tours** with images and historic facts about key attractions
3. **Providing downloadable travel information** in JSON format

## How It Works

The app uses the Toolhouse AI platform to generate travel plans and visual tours:

- The Travel Advice Agent creates detailed itineraries with daily activities, food recommendations, accommodations, and travel tips
- The Visual Tour Agent generates images and information about must-see attractions at your destination

## Getting Started

### Requirements

- Python 3.7 or higher
- Streamlit
- Required Python packages (listed in `requirements.txt`)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/travel-advisor.git
   cd travel-advisor
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run streamlit_app.py
   ```

## How to Use

1. **Enter your travel details**:
   - Destination (e.g., "Rome", "Tokyo", "Paris")
   - Your age (e.g., "20", "40", "80")
   - Trip duration in days (e.g., "2 Days", "5 Days", "7")

2. **Click "Get Travel Advice"** to generate your personalized travel plan

3. **Review your travel plan**:
   - Daily itineraries
   - Food recommendations
   - Accommodation options
   - Travel tips

4. **Click "Enter Visual Tour"** to see images and information about key attractions

5. **Download or copy** your travel plan and visual tour data if needed

## Features

- **Personalized Itineraries**: Get daily activities tailored to your age and trip duration
- **Local Recommendations**: Discover food, accommodations, and insider tips
- **Visual Exploration**: See images and learn historic facts about key attractions
- **Responsive Design**: Works on desktop and mobile devices
- **JSON Export**: Download your travel plans for offline use

## API Access

This app uses the Toolhouse AI API. The app comes with a demo API key, but for production use, you should replace it with your own key:

1. Get an API key from [Toolhouse AI](https://api.toolhouse.ai)
2. Replace the API key in the code:
   ```python
   headers = {
       "Authorization": "Bearer YOUR_API_KEY_HERE",
       "Content-Type": "application/json"
   }
   ```

## Troubleshooting

- **Slow Response Time**: The AI generation can take 10-30 seconds; please be patient
- **Error Messages**: If you see an error, try refreshing the page or checking your internet connection
- **Missing Images**: If images don't load in the visual tour, try regenerating the tour

## License

This project is licensed under the MIT License - see the LICENSE file for details.
