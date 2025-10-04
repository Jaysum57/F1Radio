# 🏁 F1Radio Discord Bot

A Discord bot that automatically fetches and shares Formula 1 team radio communications from live races and practice sessions. Built with Python and the OpenF1 API, this bot delivers real-time F1 team radio directly to your Discord server with rich embeds and audio files.

## ✨ Features

- **🎵 Direct Audio Upload**: Downloads and uploads MP3 team radio files directly to Discord
- **📡 Real-time Monitoring**: Automatically checks for new team radio every 2 minutes during sessions
- **📋 Rich Embeds**: Beautiful Discord embeds with driver info, timestamps, and session details
- **🎯 Targeted Commands**: Get radio for specific drivers or sessions on demand
- **🔒 Secure Configuration**: Environment-based configuration with `.env` file support
- **⚡ Fast & Simple**: No external dependencies or audio conversion required
- **🛡️ Error Handling**: Graceful fallbacks with MP3 links if uploads fail

## 🎮 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!radio [driver] [session]` | Get team radio data (optional parameters) | `!radio 44 latest` |
| `!latest_radio` | Get the most recent team radio | `!latest_radio` |
| `!driver_radio <number>` | Get all radio for a specific driver | `!driver_radio 44` |
| `!test_audio` | Test audio upload with sample file | `!test_audio` |
| `!help_radio` | Show all available commands | `!help_radio` |

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/F1Radio.git
   cd F1Radio
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Discord bot token and channel ID
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
DISCORD_TOKEN=your_discord_bot_token_here
CHANNEL_ID=your_discord_channel_id_here
```

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Your Discord bot token | ✅ |
| `CHANNEL_ID` | Discord channel ID for auto-posting | ✅ |

## 📱 How It Works

1. **📋 Information First**: Bot sends rich embed with driver number, timestamp, and session info
2. **📥 Download Process**: Downloads MP3 file from OpenF1 API temporarily
3. **🎵 Audio Upload**: Uploads MP3 directly to Discord for native playback
4. **🧹 Cleanup**: Automatically removes temporary files after upload

## 🔧 Technical Details

- **API Source**: [OpenF1 API](https://openf1.org/) for real-time F1 data
- **Audio Format**: Native MP3 support (no conversion required)
- **File Limits**: Respects Discord's 25MB file size limit
- **Background Tasks**: Automated monitoring every 2 minutes
- **Error Handling**: Graceful fallbacks with direct MP3 links

## 📊 API Endpoints Used

- `GET /v1/team_radio` - Fetches team radio communications
  - Parameters: `session_key`, `driver_number`
  - Returns: Array of radio objects with metadata and recording URLs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenF1](https://openf1.org/) for providing the excellent F1 data API
- [discord.py](https://github.com/Rapptz/discord.py) for the Discord API wrapper
- Formula 1 for the amazing sport and data

