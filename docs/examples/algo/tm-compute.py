# Execute Temporal Memory algorithm over active mini-columns.
tm.compute(activeColumnIndices, learn=True)
activeCells = tm.getActiveCells()
print activeCells
