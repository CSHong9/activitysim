# ActivitySim
# See full license in LICENSE.txt.

import os
import logging

import orca
import pandas as pd

from activitysim import activitysim as asim
from activitysim.defaults import tracing
from .util.mandatory_tour_frequency import process_mandatory_tours


logger = logging.getLogger(__name__)


@orca.injectable()
def mandatory_tour_frequency_spec(configs_dir):
    f = os.path.join(configs_dir, 'configs', "mandatory_tour_frequency.csv")
    return asim.read_model_spec(f).fillna(0)


@orca.step()
def mandatory_tour_frequency(set_random_seed,
                             persons_merged,
                             mandatory_tour_frequency_spec):
    """
    This model predicts the frequency of making mandatory trips (see the
    alternatives above) - these trips include work and school in some combination.
    """

    choosers = persons_merged.to_frame()
    # filter based on results of CDAP
    choosers = choosers[choosers.cdap_activity == 'Mandatory']
    logger.info("%d persons run for mandatory tour model" % len(choosers))

    # trace.print_summary('mandatory_tour_frequency choosers',
    #                     choosers.workplace_taz, describe=True)

    choices, _ = asim.simple_simulate(choosers, mandatory_tour_frequency_spec)

    # convert indexes to alternative names
    choices = pd.Series(
        mandatory_tour_frequency_spec.columns[choices.values],
        index=choices.index).reindex(persons_merged.local.index)

    tracing.print_summary('mandatory_tour_frequency', choices, value_counts=True)

    orca.add_column("persons", "mandatory_tour_frequency", choices)


"""
This reprocesses the choice of index of the mandatory tour frequency
alternatives into an actual dataframe of tours.  Ending format is
the same as got non_mandatory_tours except trip types are "work" and "school"
"""


@orca.table(cache=True)
def mandatory_tours(persons):
    persons = persons.to_frame(columns=["mandatory_tour_frequency",
                                        "is_worker"])
    persons = persons[~persons.mandatory_tour_frequency.isnull()]
    return process_mandatory_tours(persons)


# broadcast mandatory_tours on to persons using the person_id foreign key
orca.broadcast('persons', 'mandatory_tours',
               cast_index=True, onto_on='person_id')
orca.broadcast('persons_merged', 'mandatory_tours',
               cast_index=True, onto_on='person_id')
