# Minecraft Server Manager

## Overview

The **Minecraft Server Manager** is a Python-based tool designed to simplify the management of a Minecraft server and its associated resources. This script allows users to start, stop, restart the server and manage backup operations with ease. Additionally, it features scheduling capabilities for automatic backups and server shutdowns, as well as sending messages to players.

## Features

- Start, stop, and restart Minecraft server and Playit tunnel.
- Create and load backups of the Minecraft world.
- Schedule automatic backups and server shutdowns.
- Send messages to players in-game.
- View logs and currently scheduled tasks.

## Requirements

- Python 3.x
- Required Python packages: `schedule`
- Access to a Minecraft server

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/minecraft-server-manager.git
   cd minecraft-server-manager
   ```

2. Install required Python packages:
   ```bash
   pip install schedule
   ```

3. Ensure that you have the necessary scripts (`start_mc.py`, `stop_mc.py`, `start_tunnel.py`, `stop_tunnel.py`, `backup.py`, and `load_backup.py`) in the `scripts` directory.

4. Configure the `config.ini` file according to your server's specifications.

## Usage

To run the manager, execute the following command in your terminal:

```bash
python manager.py
```

### Command List

- `sa`: Start the Minecraft server and Playit tunnel.
- `qa`: Stop the Minecraft server and Playit tunnel.
- `ra`: Restart the Minecraft server and Playit tunnel.
- `smc`: Start the Minecraft server.
- `qmc`: Stop the Minecraft server.
- `rmc`: Restart the Minecraft server.
- `st`: Start the Playit tunnel.
- `qt`: Stop the Playit tunnel.
- `rt`: Restart the Playit tunnel.
- `backup`: Create a backup of the Minecraft world.
- `load`: Load the latest backup.
- `log`: Show the latest server log.
- `auto`: Toggle the autobackup setting.
- `sqa <minutes>`: Schedule server stop after a delay.
- `wsqa <minutes>`: Warn players and schedule a stop after a delay.
- `rs <task_id>`: Remove a scheduled task by ID.
- `ss`: Show currently scheduled tasks.
- `s <message>`: Send a message to all players in the server.
- `help`: Show this help message.
- `exit`: Exit the program.

## Logging

The manager logs its operations to a file named `ManagerLog.txt`, located in the base directory. Review this file for insights into the actions taken by the manager.

## Contribution

Contributions are welcome! Please submit a pull request or open an issue to discuss improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or suggestions, please contact the repository owner.
