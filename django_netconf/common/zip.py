import os
import zipfile

import logging

logger = logging.getLogger(__name__)


def zipper(sys_path, archive_name):
    try:
        os.listdir(sys_path)
    except FileNotFoundError:
        logger.error('Directory {} does not exists!'.format(sys_path))
        return False
    if os.listdir(sys_path):
        os.chdir(sys_path)
        logger.info('Creating ZIP archive {} in {}'.format(archive_name, sys_path))
        zip_archive = zipfile.ZipFile(archive_name, mode='x')
        for file in os.listdir(sys_path):
            try:
                logger.info('Appending file {} to archive {}'.format(file, archive_name))
                zip_archive.write(file)
            except RuntimeError as err:
                logger.error('While writing file {} to archive {}, got RuntimeError {}'.format(file, archive_name, err))
                return False
        zip_archive.close()
        logger.info('Closing ZIP archive {}'.format(archive_name))
        return True
    else:
        logger.error('Directory {} is empty!'.format(sys_path))
        return False
