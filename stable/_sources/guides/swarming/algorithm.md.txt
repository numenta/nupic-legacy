# The Swarming Algorithm

## Overview
This document describes the algorithm used by swarming to determine the best model for a given dataset. Please see the document [Running Swarms](Running-Swarms) for detailed instructions on how to configure and run swarms.

Swarming works by creating and trying multiple different models on a dataset and outputting the parameters for the one model that performed the best (generated the lowest error score). There are a number of factors that swarming considers when creating potential models to evaluate, including which fields from the dataset should be included, which model components should be used (encoders, spatial & temporal poolers, classifier, etc.), and what parameter values should be chosen for each component.

The potential search space for a model is typically huge. For example, you might have a swarm that has 5 potential fields to include, 3 model component choices, and a dozen parameters to optimize. Trying out all possible models from this space is prohibitively expensive, so swarming takes a dynamic approach and intelligently narrows down the search space as it progresses in order to zero in on a good performing model as quickly as possible.

Swarming can run across multiple processes. With N available processes, swarming can run N models simultaneously and make the swarm run that much faster. Swarming uses a de-centralized approach to managing the worker processes: there is no central controller process. Rather, each worker process reads and writes to a central database in order to publish the results on its models and get the results on all other models that were evaluated by other workers. This design is fault tolerant in that any worker can die or come online in the middle of a swarm and the swarm will continue running seamlessly. It thus enables high availability if the workers are spread across multiple machines and the database configured with a live backup.

## Field Search Logic
The field search logic is the outer loop of the swarming process. Swarming takes a somewhat greedy approach to selecting fields to include in the model. The overall search is organized into “sprints”. Each sprint corresponds to the number of fields that are included in the model minus 1. For sprint #0, which runs first, we try all possible single field models (A, B, C, D, …). From the best performing field in sprint #0, we build up and generate the 2-field models for sprint #1 (BA, BC, BD, BE, … if the best field from sprint #0 was field B). This process is continued to generate subsequent sprints until the error rate stops improving, at which point the swarm ends.

For sprint #0, all possible single fields are evaluated. For sprint #1 and subsequent sprints, only the top N (the default is 5, set via a configuration variable) fields from sprint #0 are considered. This keeps the swarm to a manageable size even if the dataset contains many, many fields.

Each sprint contains one or more “mini-swarms” (MS). There is one MS for each field combination in the sprint. For each MS, we evaluate multiple models (typically dozens) and eventually settle in on the best model found for that particular field combination.  Within an MS, swarming will search over the parameter space and determine which model components to include in the model as well as the optimal values for each of the parameters in each component. The logic used within an MS is described below in the sections entitled “Choosing Scalar Parameter Values” and “Choosing Enumerated Parameter Values”.

For prediction or anomaly detection models, the predicted field is always a member of the set of fields evaluated during the sprints, but its ultimate selection is optional and it may or may not end up being present in the best model. The fields evaluated during the sprints are fed into the bottom of the network (typically they end up going directly into the Spatial Pooler (SP) after being encoded). Regardless if the predicted field ends up being one of the fields ultimately chosen to enter the bottom of the network, it is _always_ sent through a separate pathway directly to the classifier’s classifier input. This pathway is used for training the classifier only (it provides the “expected output” value for the classifier) and makes use of a separate, dedicated encoder. Since this pathway is required, it is outside of the field search logic.

For spatial classification models, the only difference in the field search logic is that the predicted field is _not_ included in the list of fields to evaluate. Since we are trying to produce the predicted field at time t given the other inputs at time t, the predicted field is not known yet and can not be fed into the bottom of the network. It is still fed into the classifier’s classifier input though through the dedicated pathway described in the previous paragraph so that the classifier can learn. During inference, the classifier ignores this input.

## Choosing Scalar Parameter Values
This section describes the logic used within an MS to settle in on the best values for the scalar parameters of a model. This includes both integer and floating-point parameters.

Each MS uses a Particle Swarm Optimization (PSO) algorithm to find the optimal values for the scalar parameters. In a particle swarm, a number of particles (in this case models) are created initially. They are initially placed spread out within the parameter space and given random velocities. Each particle then evaluates its position with the parameter space (runs the model) and produces a fitness score (the result on the model’s error metric). From this fitness score and the fitness scores of the other particles, the particle then chooses a new position and the process is repeated. Once all particles have settled in and the global best fitness score stops improving, the MS ends.

When choosing a new position, a particle considers both the global best position discovered so far (from among all particles in that MS) and the local best position (the best position seen by itself) discovered so far. It then moves to a new position that is a blend of the global and local best. The farther a particle is from the local or global best, the faster it will move. There is also a random component introduced to help alleviate the chance of a particle getting stuck in a local minimum.

The full expression of the particle position update logic is as follows:

	vi = vi + ϕ1*rnd()*(pi-xi)+ ϕ2*rnd()*(gbest-xi)
	xi = xi + vi

Here, vi and xi represent the velocity and position of particle i. The new velocity of the particle is based on the old velocity, plus a weighted contribution of its distance from the local best (pi) and a weighted contribution from the global best (gbest). The new position is then computed as the old position plus the velocity.

In the PSO logic, each particle is initially assigned a unique ID, which stays with it for the lifetime of the particle as it moves around the parameter space. A particle’s initial position is labeled generation 0. Each time the particle chooses a new position; its generation index is incremented. The MS continues to evaluate new generations until the global best stops improving, at which point the MS ends.

When a user launches a swarm, they can set the swarm size to either “small”, “medium” or “large”. Currently, a “small” swarm creates just one particle per MS, a “medium” swarm creates 5 particles per MS, and a “large” swarm creates 15 particles per MS. Having more particles in an MS allows the logic to search the space more completely and can often yield a better performing model.

## Choosing Enumerated Parameter Values
This section describes the logic used within an MS to settle in on the best values for the enumerated parameters of a model. An example of an enumerate parameter is a Boolean parameter whose possible values are just true and false. Another example is a parameter that could take one of a list of possible values such as: [“scalar”, “delta”, “adaptive”].

Enumerated parameters are also used to represent high-level component choices in the model. For example, there could be a parameter called “includeSP” with possible values of true and false that drives whether or not a spatial pooler is included in the model. Or, you could have an enumerate parameter which decides which type of classifier to use (for example: [“knn”, “svm”]).

For each enumerated parameter value, swarming keeps track of the average error score seen when that particular value has been chosen. For example, if a parameter has possible values of [“A”, “B”, “C”], we might have seen an average error score of 0.2 when “A” was chosen, 0.1 when “B” was chosen, and 0.5 when “C” was chosen. When choosing a value for a new candidate model, we choose a new value using a weighted probability: the value choice with the lowest error score (in this case “A”) is given the highest probability of being chosen. The probability assigned to each choice is inversely proportional to its average error score.

## Speculative Execution
In order to fully utilize all of the worker processes provided to a swarm, swarm workers may occasionally make use of “speculative execution”. By default, speculative execution is enabled but it can be turned off via a configuration setting.

Say for example you are running a medium swarm on a dataset with 3 fields. In a medium swarm, 5 particles are created per MS. In this example, there are 3 MS’s in sprint #0 and each will be running 5 particles. If you are given more than 15 processes to use, what should the extra processes do? If speculative execution is off, they will simply be wasted because they don’t know what to do: we don’t yet know the global best position of each particle in generation 0 of each MS, so we can’t generate a particle in the next generation. In addition, we don’t yet know the best field from sprint 0, so we can’t build the field combinations for sprint 1.  

With speculative execution, if extra workers are available, those workers will speculate and create new particles even before we know the final results from earlier sprints or generations.

When an extra worker is trying to create a new model, it first tries to generate the next generation of a particle that has completed in the current sprint. If at least one particle has completed generation N, then that particle will be moved to a new position (generation N+1) even if we don’t yet have the results from all the other particles from generation N. In this case, we are updating the particle’s position to generation N+1 before we have knowledge of the final global best for generation N.

If no particles have completed yet in the current sprint, then the worker will jump ahead and start creating particles in the next sprint. Since we don’t yet know the best field combination from current sprint, the logic generates new field combinations based on _all_ the field combinations from the current sprint. For example, if sprint 0 has single field MS’s [“A”, “B”, “C”], then new field combinations will be generated for sprint 1 of [“AB”, “AC”, “BC”]. Without speculative execution, we would first wait to determine the best single field from sprint 0 and only build up 2-field combinations that include that field (for example, if “A” was the best, we would have only “AB” and “AC” in sprint 1).
