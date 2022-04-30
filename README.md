# central-asia-storage
This repository hosts data and scripts used to build the energy-water system model of Central Asia,
used in publication [Zakeri et al. (2022)] (https://doi.org/10.1016/j.est.2022.104587).
This model is built using MESSAGEix, an open-source energy systems optimization framework, which has been
long used for national, regional, and global integrated assessment and energy planning.
For more information about the modeling tool, please see [MESSAGEix documentation](https://docs.messageix.org/en/stable/index.html).

The purpose of this Github project is to share the model and data openly with interested users
with the hope that this can be useful for their analysis, further development of the model,
and/or receiving feedback. Please use Github features "issues" and "pull-requests" directly,
if you want to suggest improvements in the code and update of data.
For other matters please contact (zakeri@iiasa.ac.at).

## Description of the model
The Central Asia model is a multi-node energy-water system representing five countries in the region, i.e.,
Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan, as seperate model regions.
These countries are interconnected through electricity transmission lines and water rivers.

The energy-water model presented here include the following sub-systems and sectors:
- Fossil fuel extraction, upstream supply, refineries, and T&D
- External energy trade links, e.g., oil export and import with the rest of the world
- Renewable energy potentials, technologies, and different quality grades
- Full power system model, including generation, T&D, balancing, and ancillary service needs
- Electricity demand in buildings and the industry separately
- Transboundary water river flows, upstream water flow, hydropower dams, spillage, and downstream water demand
- Flexibility, curtailment, and balancing needs related to variable renewable energy (wind and solar)

The model is built based on standard model structure of IIASA's MESSAGEix-GLOBIOM. 
Hence, more information on the structure of the model can be found [here](https://docs.messageix.org/projects/global/en/latest/).

## How to check the input data?
You can find all the data used for building this model under the folder ["data"](https://github.com/iiasa/central-asia-storage/data).
There is a complete version of data for modeling, and a shorter version for policy makers. Please check the definitions before working with 
each dataset. While values are the same, the units are slightly different in the mentioned datasets. For example, the unit of energy in the model
data is GWa (Gigawatt-annum, equal to 8.76 TWh), as this is easier for the model parameterization. However, this unit is TWh for electricity and PJ
for other energy carriers in the data presented for policy makers, as these are more familiar units in national energy balances and statistics.

## How to build a water-energy model for Central Asia?
In this repository, there are data and scripts that can help you for:
- Building the water-energy model of Central Asia ([see tutorial for Baseline]
(https://github.com/iiasa/central-asia-storage/scripts/interface_baseline.ipynb)) by using the data stored
[here](https://github.com/iiasa/central-asia-storage/data).
- Model renewable energy policies in the region ([see tutorial for Renewables]
(https://github.com/iiasa/central-asia-storage/scripts/interface_renewable.ipynb)).
- Model the functionality of seasonal pumped hydropower storage (SPHS) in the region ([see tutorial for Pumpedhydro]
(https://github.com/iiasa/central-asia-storage/scripts/interface_pumpedhydro.ipynb)).
- Represent carbon emissions targets in the region ([see here]
(https://github.com/iiasa/central-asia-storage/scripts/interface_pumpedhydro.ipynb)).
- Analyze and visualize the scenarios mentioned above, and other scenarios that interest you.

Please go through the tutorials with the order mentioned above. These tutorials are designed
for those familiar with the MESSAGEix model. If you have recently started using MESSAGEix, please make yourself 
familiar with [MESSAGEix tutorials](https://github.com/iiasa/message_ix/tree/main/tutorial/westeros), which are excellent examples for getting started.

Please contact us if you have any questions or comments, either through Github or (zakeri@iiasa.ac.at).