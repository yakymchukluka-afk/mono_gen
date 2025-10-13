# Latent Walk Video Generator UI

A simple, responsive web interface for generating latent walk videos using the FastAPI service.

## Features

- **Step 1**: Configure and initiate video generation
- **Step 2**: Preview generated video with download option
- **Responsive design**: Works on desktop and mobile
- **Configurable**: Easy API endpoint and authentication setup
- **Error handling**: User-friendly error messages

## Local Testing

### 1. Copy configuration file

```bash
cd ui
cp config.example.js config.js
```

### 2. Edit configuration

Edit `config.js` to point to your API:

```javascript
window.config = {
    // For local API testing
    API_BASE: "http://localhost:8888",
    API_KEY: ""  // Leave empty if no auth
};
```

### 3. Start local server

```bash
# Using Python (recommended)
python -m http.server 3000

# Or using Node.js
npx serve .

# Or using any other static file server
```

### 4. Open in browser

Navigate to `http://localhost:3000`

## Configuration Options

### API_BASE
- **Local development**: `http://localhost:8888`
- **RunPod deployment**: `https://your-runpod-id-0-0-0-0-8888.proxy.runpod.net`

### API_KEY
- Leave empty (`""`) if no authentication is required
- Set to your API key if the backend requires authentication

## Usage

1. **Configure video parameters**:
   - Duration (5-120 seconds)
   - FPS (10-60)
   - Resolution (256x256, 512x512, or 1024x1024)

2. **Click "Generate Video"**:
   - The button shows loading state during generation
   - Process typically takes 1-3 minutes

3. **Preview and download**:
   - Video automatically loads in the preview player
   - Click "Download Video" to save the MP4 file
   - Click "Generate New Video" to start over

## Error Handling

The UI handles various error scenarios:

- **Network errors**: Connection to API failed
- **API errors**: Backend returned error response
- **Validation errors**: Invalid input parameters
- **Video load errors**: Generated video couldn't be loaded

All errors are displayed with user-friendly messages and retry options.

## Browser Compatibility

- **Modern browsers**: Chrome, Firefox, Safari, Edge
- **Features used**: Fetch API, ES6 modules, CSS Grid
- **Video format**: MP4 (H.264 codec)

## Development

### File Structure

```
ui/
├── index.html          # Main HTML file
├── styles.css          # CSS styles
├── main.js            # JavaScript logic
├── config.example.js  # Configuration template
├── config.js          # Actual configuration (not in git)
└── README.md          # This file
```

### Key Functions

- `loadConfig()`: Loads configuration from config.js
- `generateVideo()`: Makes API call to generate video
- `showVideoPreview()`: Displays generated video
- `showError()`: Shows error messages to user

### Customization

To customize the UI:

1. **Styling**: Edit `styles.css`
2. **Layout**: Modify `index.html`
3. **Behavior**: Update `main.js`
4. **API integration**: Modify the fetch calls in `main.js`