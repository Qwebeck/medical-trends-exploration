# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

from src.data.make_bdl import make_bdl


@click.command()
def main():
    """ Runs scripts to collect data and stores (../raw).
    """
    logger = logging.getLogger(__name__)
    project_dir = Path(__file__).resolve().parents[2]
    make_bdl(project_dir / 'data' / 'raw' / 'medical_staff_stats_bdl', should_overwrite=False)
    logger.info('making final data set from raw data')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
