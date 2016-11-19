from pyrtitions import get_partitions, get_uuids_and_labels, generate_mountpoint, get_device_sizes, get_size_from_block_count, get_mounts, label_filter, pprint_partitions


if __name__ == "__main__":             
    pprint_partitions(get_partitions())
