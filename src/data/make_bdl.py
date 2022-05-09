import logging
from pathlib import Path
import pandas as pd
from src.data.gus_retriever import Level, get_complete_gus_data


def make_bdl(save_to_folder: Path, should_overwrite: bool):
    medical_staff = {
        'overall_medical_staff': 74067,
        'women_medical_staff': 74071,
        'men_medical_staff': 74075
    }
    nurses = {
        'overall_nurses': 74087,
        'nurses_with_master_degree': 74091
    }
    midwives = {
        'overall_midwives': 74085,
        'midwives_with_master_degree': 74089
    }
    rescuers = {
        'overall': 395367
    }
    variables = {
        'medical_staff': medical_staff,
        'nurses': nurses,
        'midwives': midwives,
        'rescuers': rescuers
    }
    for variable_set_name, variable_set in variables.items():
        for var_name in variable_set:
            logging.info(f'obtaining {var_name}')
            year_range = range(2010, 2022)
            file_path = save_to_folder / 'medical_staff_stats_bdl' / \
                variable_set_name / f'{var_name}_summary.csv'
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True)
            if file_path.exists() and not should_overwrite:
                logging.info(f"Skipping {var_name} because it already exists")
                continue
            data = _collect_data_over_years(
                variable_set[var_name], var_name, year_range)
            data.to_csv(file_path)


def _collect_data_over_years(var_id, var_name, year_range) -> pd.DataFrame:
    variable_values_over_years = pd.DataFrame(columns=[var_name])
    for year in year_range:
        data = get_complete_gus_data(
            Level.COUNTRY, [var_id], year, {var_name: var_id})
        if data is not None and var_name in data.columns:
            variable_values_over_years.loc[year,
                                           var_name] = data.loc[0, var_name]
        else:
            logging.info(f"No info provided for year {year}")
    return variable_values_over_years
