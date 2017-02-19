"""
A class for using depth-limited DFS to try to find improvements to a schedule.
"""


class SearchOptimizer:
    def __init__(self, manipulator):
        self.manipulator = manipulator
        self.roomslots = []
        for room in manipulator.schedule.classrooms.itervalues():
            self.roomslots += room.availability

    def optimize_section(self, section, depth):
        """Tries to schedule (if it is not scheduled) or move (if it is already
        scheduled) the specified section by moving or unscheduling other
        sections, searching up to the specified depth. Returns the actions
        done."""
        if depth == 0:
            return []
        best_score = self.manipulator.scorer.score_schedule()
        best_actions = []
        # Explore all possible roomslots to move to.
        for roomslot in self.roomslots:
            # First, figure out what slots we need.
            needed_slots = roomslot.room.get_roomslots_by_duration(
                    roomslot, section.duration)
            other_sections = []
            proposed_actions = []
            failed = False
            # Kick everyone else out of those slots.
            for needed_slot in needed_slots:
                if needed_slot.assigned_section is not None:
                    other_section = needed_slot.assigned_section
                    other_sections.append(other_section)
                    success = \
                        self.manipulator.unschedule_section(other_section)
                    if not success:
                        self.revert(len(proposed_actions))
                        failed = True
                        break
                    self.update_proposed_actions(proposed_actions)
            if failed:
                continue

            # Move into the slots we want.
            if section.is_scheduled():
                success = self.manipulator.move_section(section, roomslot)
            else:
                success = self.manipulator.schedule_section(section, roomslot)
            if not success:
                self.revert(len(proposed_actions))
                continue
            self.update_proposed_actions(proposed_actions)

            # Recurse on each evicted section.
            for other_section in other_sections:
                proposed_actions += \
                        self.optimize_section(other_section, depth - 1)
            # Compute the score.
            new_score = self.manipulator.scorer.score_schedule()
            if new_score > best_score:
                best_score = new_score
                best_actions = proposed_actions

            self.revert(len(proposed_actions))

        for action in best_actions:
            self.manipulator.perform_action(action)
        return best_actions

    def update_proposed_actions(self, proposed_actions):
        """Append the last item in history to the proposed actions."""
        proposed_actions.append(self.manipulator.history[-1])

    def revert(self, n):
        """Undo the last n actions."""
        for action in xrange(n):
            self.manipulator.undo()
