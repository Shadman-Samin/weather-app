# Atmos - Premium Weather Dashboard

Atmos is a high-quality, production-ready weather application featuring a modern glassmorphism design, real-time city autocomplete, and interactive maps.

## ✨ Features

- **Glassmorphism UI**: A stunning, premium interface using modern CSS techniques like `backdrop-filter`.
- **Real-time Autocomplete**: Search for cities with instant suggestions including state and country names.
- **5-Day Forecast**: Accurate weather forecasts for the next five days, parallelized for maximum performance.
- **Interactive Map**: Live weather maps powered by Leaflet.js with dynamic theme-switching.
- **Dynamic Backgrounds**: High-quality city imagery fetched dynamically via the Pexels API.
- **Light/Dark Mode**: Smooth theme transitions with persistent state via cookies.
- **Geolocation**: One-click current location weather tracking.
- **Search History**: Quick access to your recently searched locations.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+)
- **APIs**:
  - [OpenWeatherMap](https://openweathermap.org/api) (Weather & Geocoding)
  - [Pexels](https://www.pexels.com/api/) (Dynamic Backgrounds)
- **Libraries**: Leaflet.js (Maps), FontAwesome (Icons), Google Fonts (Outfit)

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Shadman-Samin/weather-app.git
   cd weather-app
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add your API keys:
   ```env
   API_KEY=your_openweathermap_api_key
   PEXELS_API_KEY=your_pexels_api_key
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

## ⚡ Performance Optimizations

- **Parallel API Fetching**: Uses Python's `ThreadPoolExecutor` to fetch forecast and background data simultaneously, reducing page load times by ~40%.
- **Debounced Search**: Optimized autocomplete input to minimize redundant API calls while typing.
- **CSS Stacking Contexts**: Optimized map rendering for smooth performance inside glass panels.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
