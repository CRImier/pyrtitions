import os
import shlex
import string

__version__ = '0.2.0'

def get_uuids_and_labels():
    """
      Returns a list of available partitions. Each partition is a dictionary with "uuid" and "path" keys (optionally, also "label").
      Example: [{"uuid":"5OUU1DMUCHUNIQUEW0W", "path":"/dev/sda1"}, {"label":"VeryImportantDrive", "uuid":"MANYLETTER5SUCH1ONGWOW", "path":"/dev/sdc1"}]
    """
    partitions = []
    labels = {}
    dbu_dir = "/dev/disk/by-uuid/"
    dbl_dir = "/dev/disk/by-label/"
    try:
        parts_by_label = os.listdir(dbl_dir)
    except OSError:
        parts_by_label = []
    parts_by_uuid = os.listdir(dbu_dir)
    for label in parts_by_label:
        #Getting the place where symlink points to - that's the needed "/dev/sd**"
        path = os.path.realpath(os.path.join(dbl_dir, label))
        labels[path] = label
        #Makes dict like {"/dev/sda1":"label1", "/dev/sdc1":"label2"}
    for uuid in parts_by_uuid:
        path = os.path.realpath(os.path.join(dbu_dir, uuid))
        details_dict = {"uuid":uuid, "path":path}
        if path in labels.keys():
            details_dict["label"] = labels[path]
        partitions.append(details_dict)
    return partitions

def get_size_from_block_count(block_count_str, size_step=1000, sizes = ["K", "M", "G", "T"], format_spec=":2.2f"):
    """Transforms block count (as returned by /proc/partitions and similar files) to a human-readable size string, with size multiplier ("K", "M", "G" etc.) appended.

    Kwargs:

        * ``size_step``: size of each multiplier
        * ``sizes``: list of multipliers to be used
        *``format_spec``: value formatting specification for the final string
    """
    block_count = float(block_count_str)
    size_counter = 0
    while block_count >= float(size_step):
        block_count /= size_step
        size_counter += 1
    return ("{"+format_spec+"}{}").format(block_count, sizes[size_counter])

def get_device_sizes():
    """ Gets partition sizes for all the partitions/block devices available in /proc/partitions.

    Outputs a dictionary of path_basename:["human-readable-size", "block_count_string", "major_number_integer", "minor_number_integer"] entries."""
    with open("/proc/partitions", "r") as f:
        lines = f.readlines()
    info_dict = {}
    lines = lines[1:] #First line is the header
    for line in lines:
        line = line.strip()
        if line:
            major, minor, block_count_str, name = line.split()
            hr_size = get_size_from_block_count(block_count_str)
            info_dict[name] = [hr_size, block_count_str, int(major), int(minor)]
    return info_dict

def get_mounts(mounts_file="/etc/mtab"):
    """Gets all the mounted partitions.
    Outputs a dictionary of path:["mountpoint", "type", "mount options"] entries.

    ``mounts_file`` allows you to specify another file to read from."""
    mounted_partitions = {}
    with open(mounts_file, "r") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line:
            elements = shlex.split(line) #Avoids splitting where space character is enclosed in " " or ' '
            if len(elements) != 6:
                print("Couldn't decypher following line: "+line)
                break
            device_path = elements[0]
            mountpoint = elements[1]
            part_type = elements[2]
            mount_opts = elements[3]
            #mtab is full of entries that aren't any kind of partitions we're interested in - that is, physical&logical partitions of disk drives
            #Let's try to filter entries by path
            if device_path.startswith("/dev"):
                device_path = os.path.realpath(device_path) #Can be a symlink?
                mounted_partitions[device_path] = [mountpoint, part_type, mount_opts]
    return mounted_partitions

def get_partitions():
    """Combines ``gets_uuids_and_labels``, ``get_mounts`` and ``get_device_sizes`` into one huge dictionary.

    Format is the same as for ``get_uuids_and_labels``, but with following keys added:

    * ``mounted``: True if partition is currently mounted, False if not.

        If partition is mounted, following keys are added:
        * ``part_type``: partition type as given in /etc/mtab
        * ``mount_opts``: partition mount options as given in /etc/mtab
    * `` mountpoint``: partition mountpoint (None if not mounted).
    * `` size``: partition size if detected, else None"""
    partitions = get_uuids_and_labels()
    mounted_partitions = get_mounts()
    partition_sizes = get_device_sizes()
    for entry in partitions:
         if entry["path"] in mounted_partitions:
             mpoint, ptype, opts = mounted_partitions[entry["path"]]
             entry["mounted"] = True
             entry["mountpoint"] = mpoint
             entry["part_type"] = ptype
             entry["mount_opts"] = opts
         else:
             entry["mounted"] = False
             entry["mountpoint"] = None
         basename = os.path.basename(entry["path"])
         if basename in partition_sizes:
             entry["size"] = partition_sizes[basename][0]
         else:
             entry["size"] = None
    return partitions

def generate_mountpoint(part_info, base_dir="/media"):
    """Takes a partition entry from ``get_partitions`` or ``get_uuids_and_labels`` and returns a valid (not taken by another device) mountpoint path, for example, for automatic mount purposes"""
    #We could use either label (easier and prettier)
    #Or UUID (not pretty yet always available)
    path_from_uuid = os.path.join(base_dir, part_info['uuid'])
    #We can tell that the directory we want to choose as mountpoint is OK if:
    #1) It doesn't exist, or:
    #2) Nothing is mounted there and it's empty.
    if "label" in part_info.keys():
        path_from_label = os.path.join(base_dir, part_info['label'])
        if not os.path.exists(path_from_label) or (not os.path.ismount(path_from_label) and not os.listdir(path_from_label)):
            return path_from_label
    elif not os.path.exists(path_from_uuid) or (not os.path.ismount(path_from_uuid)):
        return path_from_uuid
    else:
        #Some filesystems have really short UUIDs and I've seen UUID collisions in my scripts with cloned drives
        counter = 1
        while os.path.exists(path_from_uuid+"_("+str(counter)+")"):
            counter += 1
        return path_from_uuid+"_("+str(counter)+")"

def label_filter(label):
    """Filters passed partition labels to alphanumeric characters"""
    label_list = list(label)
    ascii_letters = string.ascii_letters+string.digits
    for char in arr_label[:]:
        if char not in ascii_letters:
            arr_label.remove(char)
    return "".join(label_list)

def pprint_partitions(partitions):
    """Pretty-prints entries from  from ``get_partitions`` or ``get_uuids_and_labels``."""
    for part in partitions:
        print("Path: "+part["path"])
        other_keys = [key for key in part.keys() if key!="path"]
        for key in other_keys:
            value = part[key]
            print("\t{}:{}".format(key, value))

def get_blockdev_major_minor(filter_virtual = True):
    """Gets all available block devices, as well as their major and minor numbers.
    Returns a dictionary of path:[major_int, minor_int].

    When ``filter_virtual`` is set to True, filters out all the virtual devices."""
    devices = {}
    blockd_dir = "/dev/block" #Contains symlinks to block devices with "major:minor"-formatted names
    blockd_links = os.listdir(blockd_dir)
    for major_minor in blockd_links:
        major, minor = map(int, major_minor.split(':'))
        device_path = os.path.realpath(os.path.join(blockd_dir, major_minor))
        devices[device_path] = (major, minor)
    if filter_virtual:
        virtual_devices = get_virtual_devices()
        devices = {k: v for k,v in devices.items() if os.path.basename(k) not in virtual_devices}
    return devices

def get_block_devices():
    """
      Returns a dictionary of all the major devices available.

      Entry format is ``device_path:{"major":major_int, size:human readable size (from ``get_device_sizes``), "blocks":block count, "partitions":[{"name":path, "minor":minor_int, "blocks":block count, "size:human readable size (from ``get_device_sizes``"}, ...]}``
    """
    #Guess I'll intentionally forget about whole-disk partitions
    devices = {}
    devices_by_major = {}
    bdevs = get_blockdev_major_minor()
    device_sizes = get_device_sizes()
    #First, creating dictionary entries for all the block devices with minor 0
    for bdev in bdevs:
        major, minor = bdevs[bdev]
        if minor == 0:
            hr_size, block_count = device_sizes[os.path.basename(bdev)][:2]
            devices_by_major[major] = {"name":bdev, "size":hr_size, "blocks":block_count, "partitions":[]}
    #Then, filling in the info dictionaries with devices with higher minor numbers for the corresponding major:0 device
    for bdev in bdevs:
        major, minor = bdevs[bdev]
        if minor != 0:
            hr_size, block_count = device_sizes[os.path.basename(bdev)][:2]
            devices_by_major[major]["partitions"].append({"name":bdev, "size":hr_size, "blocks":block_count, "minor":minor})
    #Then, remaking each dictionary to use name rather than major number as a key.
    for major in devices_by_major:
        device = devices_by_major[major]
        name = device.pop("name")
        device["major"] = major
        devices[name] = device
    return devices

def get_virtual_devices():
    """Returns all virtual device names present in the system (like loopX, ramX and whatever else is in the /sys/devices/virtual/block directory)"""
    virtual_devices = os.listdir("/sys/devices/virtual/block")
    return virtual_devices


def __main__():
    #print(get_device_sizes())
    #print(get_block_devices())
    pprint_partitions(get_partitions())

if __name__ == "__main__":
    __main__()
