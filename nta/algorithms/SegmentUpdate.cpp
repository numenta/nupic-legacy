/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */

#include <nta/utils/Log.hpp>
#include <nta/algorithms/SegmentUpdate.hpp>
#include <nta/algorithms/Cells4.hpp>

using namespace nta::algorithms::Cells4;


SegmentUpdate::SegmentUpdate()
  : _sequenceSegment(false),
    _cellIdx((UInt) -1),
    _segIdx((UInt) -1),
    _timeStamp((UInt) -1),
    _synapses(),
    _phase1Flag(false),
    _weaklyPredicting(false)
{}

SegmentUpdate::SegmentUpdate(UInt cellIdx, UInt segIdx,
                             bool sequenceSegment, UInt timeStamp,
                             const std::vector<UInt>& synapses,
                             bool phase1Flag,
                             bool weaklyPredicting,
                             Cells4* cells)
  : _sequenceSegment(sequenceSegment),
    _cellIdx(cellIdx),
    _segIdx(segIdx),
    _timeStamp(timeStamp),
    _synapses(synapses),
    _phase1Flag(phase1Flag),
    _weaklyPredicting(weaklyPredicting)
{
  NTA_ASSERT(invariants(cells));
}


//--------------------------------------------------------------------------------
SegmentUpdate::SegmentUpdate(const SegmentUpdate& o)
{
  _cellIdx = o._cellIdx;
  _segIdx = o._segIdx;
  _sequenceSegment = o._sequenceSegment;
  _synapses = o._synapses;
  _timeStamp = o._timeStamp;
  _phase1Flag = o._phase1Flag;
  _weaklyPredicting = o._weaklyPredicting;
  NTA_ASSERT(invariants());
}





bool SegmentUpdate::invariants(Cells4* cells) const
{
  bool ok = true;

  if (cells) {

    ok &= _cellIdx < cells->nCells();
    if (_segIdx != (UInt) -1)
      ok &= _segIdx < cells->__nSegmentsOnCell(_cellIdx);

    if (!_synapses.empty()) {
      for (UInt i = 0; i != _synapses.size(); ++i)
        ok &= _synapses[i] < cells->nCells();
      ok &= is_sorted(_synapses, true, true);
    }
  }

  return ok;
}
