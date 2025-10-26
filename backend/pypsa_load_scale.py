# Load and Gen Scaling
# 
# Load and gen changes based on time of day, day of the week, and weather. You can see some government data
# (https://www.eia.gov/todayinenergy/detail.php?id=42915) for some fun data.
# 
# The load changes through the day provide another interesting problem to solve if we solve everything else. This
# requires a lot of work with a solver and manipulating the model.


# Scaling in our Hawaii40 model
# 
# We can use a sine wave to approximate load variations through the day if we are:
# - min/max at 6pm/6am
# - values in model are nominal - peaks are 10% below/above nominal.
# 
# Remember that as we increase the load, we also must increase then generation. The solver doesn't automatically
# change the generation values to meet the new load. If you don't increase the generation, this "missing power" will
# magically come from the slack bus or cause the solver to fail.


def check_pf(info):
    converged = info.converged.any().any()
    max_error = info.error.max().max()
    print(f"Sim converged: {converged}")
    print(f"Max error: {max_error:.2e}")

    if ~converged:
        raise Exception("Sim didn't convert - results are garbage. Change to lpf()")


import pypsa
network = pypsa.Network()
network.import_from_csv_folder('data')
info = network.pf()
check_pf(info)


# Sanity check gen and load
# 
# The gen and load should be fairly close to each other, or something is really wrong with the model

pload_total = network.loads['p_set'].sum().round(0)
print(f"Total load in network {pload_total}")

pgen_total = network.generators['p_set'].sum().round(0)
print(f"Total gen in network {pgen_total}")


# Sanity check gen and load solution
# 
# Our solved values for gen and load should closely match the set points.

network.generators_t['p'].sum(axis=1)

network.loads_t['p'].sum(axis=1)


# Sine waves ftw
# 
# Let's create our load profile with the venerable sine wave.

import matplotlib.pyplot as plt
import numpy as np

x = np.arange(24)
f = 1/24
offset = 1136
A = 100
C = 2*np.pi/2
y = A * np.sin(2*np.pi * f * x + C) + offset
plt.plot(x, y, 'o')
plt.xlabel('hour of day')
plt.ylabel('load (MW)')
plt.grid()
plt.show()

# I changed my mind - let's normalize the sine wave between 0-1 so I can just 
# scale each gen/load
x = np.arange(24)
f = 1/24
offset = 1
A = .1
C = 2*np.pi/2
y = A * np.sin(2*np.pi * f * x + C) + offset
plt.plot(x, y, 'o')
plt.xlabel('hour of day')
plt.ylabel('load/gen fraction')
plt.grid()
plt.show()

# To a list because some days I don't trust numpy
y.round(3).tolist()


# Let's scale those loads
# 
# Now that we have the weights calculated let's apply them to the model and solve the case again. Since we have
# time varying data we should try to figure out the pypsa snapshot.
# 
# In my experience, the snapshot pattern isn't typically built into simulators. I usually have to keep track of the
# data outside of the tool.

hour = 6
scale = 1.1
print(f"Scaling load by {scale}")

network.loads.head()

# Take a moment to appreciate how each this is
# We always scale P (real) and Q (imag) together because that's how it works
network.loads['p_set'] = scale * network.loads['p_set']
network.loads['q_set'] = scale * network.loads['q_set']

# Note that p_set is lower
network.loads.head()

# Rinse and repeat for gens
network.generators['p_set'] = scale * network.generators['p_set']
network.generators['q_set'] = scale * network.generators['q_set']


# Solve and compare
# 
# Solve the new case and see if the gens/loads are actually different (spoiler alert: they better be)

info = network.pf()
check_pf(info)

# should be about 1039 = 0.9 * 1155 
network.generators_t['p'].sum(axis=1)

# Should be about 1022 = 0.9 * 1136
network.loads_t['p'].sum(axis=1)

network.lines_t['p0']
