# Home Assistant Custom Component - Sync Group

A Sync Group is a group component that synchronizes the state of its members. Currently, only light sync group is supported.

A Light Sync Group is a group of lights, that behaves exactly as a normal Home Assistant group, except for the fact that
it tries to synchronize the On/Off state of its members. If one of the members is turned on or off, all the other members
receive a command that switches them to the same state. The synchronization is made only for the main state (On/Off) and not
to the attributes (color, brightness, etc.). Apart from this, the group behaves as a normal light group. It has a state
which is derived from the state of its members and it receives `light.turn_on` and `light.turn_off` commands
as a regular light entity. When one of this commands are issued on the group entity, the attributes are forwarded
to all of the members.

## Installation

### Installation via HACS
1. Install HACS (if not already installed)
2. Open the HACS paged and click the "Integrations" section.
3. Click on the three dots on the top right corner. Select "Custom Repositories".
4. In the dialog, enter the repository URL: `https://github.com/avishorp/sync_group.git`.
   For the category, select "Integration".
5. Click "Add". HACS will download the content of the repository.
6. Search for "sync group" in HACS' integrations tab and add it.


### Manual Installation
1. Open the configuration folder of your Home Assistant installation.
2. Download or clone this repository into a separate location.
3. Copy the content of `custom_components` from the repository to the configuration
   directory. A directory named `custom_components` may already exist, the content of
   the repository is not supposed to overwrite any file stored in it (unless you are
   upgrading to a newer version).
4. Restart Home Assistant. After restart, the Light Sync Group should become available.
   See below for configuration instructions.


## Configuration

### Configuration with the UI
The Light Sync Group is a helper, like a regular group. It can be added into Home Assistant via the "Create Helper"
button. After pressing the button, select "Light Sync Group" from the menu, and then configure its name
and member entities. A "Hide Members" function is also provided and behaves identically to a regular light
group.

### Configuration with YAML
A Light Sync Group can be configured from `configuration.yaml` like this:
```yaml
light:
    - platform: light_sync_group
      entities:
          - light.member1
          - light.member2
```

