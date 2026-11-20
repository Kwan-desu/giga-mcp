# Giga-MCP

Unified local MCP server combining:
1. **Microsoft Teams** (`teams-mcp`) — chats, channels, mentions, replies, reactions, polls, token auto-refresh.
2. **APU Timetable & Classroom Finder** (`aptimetable-mcp`) — intakes, groupings, weekly timetables, free/occupied classrooms, nearby room suggestions.
3. **APU Moodle LMS** (`Moodle-MCP`) — SSO/cookie login, courses, upcoming deadlines, course materials, slide/study-material generation.

## Shared Microsoft Auto-Login (`.env`)

Edit `d:\Ai project\cool stuff\giga-mcp\.env` with your Microsoft/APU credentials:

```env
MS_EMAIL=your_email@mail.apu.edu.my
MS_PASSWORD=your_password

APU_INTAKE=APD3F2502CS(AI)
APU_GROUPING=G1
APU_STUDENT_NAME=Your Name
APU_TP_NUMBER=TP012345
```

Both **Teams** (`teams-mcp`) and **Moodle** (`Moodle-MCP`) automatically fill your email, password, and "Stay signed in?" prompt when Microsoft SSO (`login.microsoftonline.com`) opens (you only need to approve MFA/2FA if prompted). `.env` is gitignored.

## MCP Client Configuration

```json
{
  "mcpServers": {
    "giga-mcp": {
      "command": "python",
      "args": ["d:\\Ai project\\cool stuff\\giga-mcp\\server.py"]
    }
  }
}
```

> **Note:** Uses your system Python environment where `mcp`, `playwright`, `requests`, `beautifulsoup4`, `python-pptx`, `selenium`, and `python-dotenv` are installed. Existing session/cache files in each sub-project are reused automatically.
