import os
import shlex
import string

def get_partitions():
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
        #partitions is now something like 
        #[{"uuid":"5OUU1DMUCHUNIQUEW0W", "path":"/dev/sda1"}, {"label":"label1", "uuid":"MANYLETTER5SUCH1ONGWOW", "path":"/dev/sdc1"}]
    return partitions

def get_partitions_and_mounts():
    partitions = get_partitions()
    mounted_partitions = {}

    #Good source of information about mounted partitions is /etc/mtab
    mtab_path = "/etc/mtab" 
    f = open(mtab_path, "r")
    lines = f.readlines()
    f.close()
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
    return partitions

def generate_mountpoint(part_info, base_dir="/media"):
    """Generates a valid mountpoint path, for example, for automatic mount purposes"""
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
    label_list = list(label)
    ascii_letters = string.ascii_letters+string.digits
    for char in arr_label[:]:
        if char not in ascii_letters:
            arr_label.remove(char)
    return "".join(label_list)

def pprint_partitions(partitions):
    for part in partitions:
        print(part["path"])
        other_keys = [key for key in part.keys() if key!="path"]
        for key in other_keys:
            value = part[key]
            print("\t{}:{}".format(key, value))

if __name__ == "__main__":
    partitions = get_partitions_and_mounts()
    pprint_partitions(partitions)
