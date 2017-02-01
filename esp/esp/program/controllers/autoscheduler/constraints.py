# TODO: documentation on adding constraints


class BaseConstraint:
    """Abstract class for constraints."""
    default_on = True

    def check_schedule(self, schedule):
        """Returns False if an AS_Schedule violates the constraint,
        True otherwise."""
        raise NotImplementedError

    # These local checks are for performance reasons.
    def check_add_section(self, section, room, start_time, schedule):
        """Assuming that we start with a valid schedule, returns False
        if scheduling the section in the room at the start time would
        violate the constraint, True otherwise."""
        return self.check_schedule(schedule)

    def check_move_section(self, section, room, start_time, schedule):
        """Assuming that we start with a valid schedule, returns False
        if moving the already-scheduled section to the room at the start time
        would violate the constraint, True otherwise."""
        return self.check_schedule(schedule)

    def check_remove_section(self, section, schedule):
        """Assuming that we start with a valid schedule, returns False
        if unscheduling the specified section will violate the constraint,
        True otherwise."""
        return self.check_schedule(schedule)

    def check_swap_sections(self, section1, section2, schedule):
        """Assuming that we start with a valid schedule, returns False
        if swapping two sections will violate the constraint,
        True otherwise."""
        return self.check_schedule(schedule)


class CompositeConstraint(BaseConstraint):
    """A constraint which checks all the constraints you actually want."""
    def __init__(self, constraint_names):
        """Takes in a list of constraint names, as strings."""
        self.constraints = []
        available_constraints = globals()
        for constraint in constraint_names:
            self.constraints.append(available_constraints[constraint]())

    def check_schedule(self, schedule):
        return all(map(lambda c: c.check_schedule(schedule), self.constraints))

    def check_add_section(self, section, room, start_time, schedule):
        return all(map(
            lambda c: c.check_add_section(section, room, start_time, schedule),
            self.constraints))

    def check_move_section(self, section, room, start_time, schedule):
        return all(map(
            lambda c: c.check_move_section(
                section, room, start_time, schedule),
            self.constraints))

    def check_remove_section(self, section, schedule):
        return all(map(lambda c: c.check_remove_section(section, schedule),
                       self.constraints))

    def check_swap_sections(self, section1, section2, schedule):
        return all(map(
            lambda c: c.check_swap_sections(section1, section2, schedule),
            self.constraints))


class ContiguousConstraint(BaseConstraint):
    """Multi-hour sections may only be scheduled across
    contiguous timeblocks."""
    pass  # TODO


class LunchConstraint(BaseConstraint):
    """Multi-hour sections can't be scheduled over both blocks of lunch."""
    pass  # TODO


class ResourceConstraint(BaseConstraint):
    """If a section demands an unprovided required resource."""
    pass  # TODO


class RestrictedRoomConstraint(BaseConstraint):
    """If a room demands only sections of a particular type
    (e.g. if only computer classes may be scheduled in computer labs)"""
    pass  # TODO


class RoomAvailabilityConstraint(BaseConstraint):
    """Sections can only be in rooms which are available."""
    pass  # TODO


class RoomConcurrencyConstraint(BaseConstraint):
    """Rooms can't be double-booked."""
    pass  # TODO


class SectionLengthConstraint(BaseConstraint):
    """Sections must be scheduled for exactly their length.
    This also accounts for not scheduling a section twice,
    in conjunction with consistency constraints."""
    pass  # TODO


class TeacherAvailabilityConstraint(BaseConstraint):
    """Teachers can only teach during times they are available."""
    pass  # TODO


class TeacherConcurrencyConstraint(BaseConstraint):
    """Teachers can't teach two classes at once."""
    pass  # TODO