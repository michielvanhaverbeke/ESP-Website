import datetime

import esp.program.controllers.autoscheduler.models as models
from esp.cal.models import Event
from esp.program.models.class_ import ClassSubject
from esp.resources.models import Resource, ResourceType, ResourceRequest
from esp.program.tests import ProgramFrameworkTest


class ScheduleTest(ProgramFrameworkTest):
    def setUp(self):
        # Explicit settings, but we'll also add a new timeslot, room and class.
        # The new class and room will request and have a new resource,
        # respectively.
        # This increases the complexity of the program for stricter testing.
        settings = {
            'num_timeslots': 6,
            'timeslot_length': 50,
            'timeslot_gap': 10,
            'room_capacity': 30,
            'num_categories': 2,
            'num_rooms': 4,
            'num_teachers': 5,
            'classes_per_teacher': 2,
            'sections_per_class': 1,
            'num_students': 0,
            'num_admins': 1,
            'program_type': 'TestProgram',
            'program_instance_name': '2222_Summer',
            'program_instance_label': 'Summer 2222',
            'start_time': datetime.datetime(2222, 7, 7, 7, 5),
        }
        extra_settings = {
            "extra_timeslot_start": datetime.datetime(2222, 7, 8, 7, 5),
            "extra_room_capacity": 151,
            "extra_room_availability": [1, 2, 4, 5],  # Timeslot indices
            "extra_class_teachers": [0, 3],  # Teacher indices
            "extra_class_sections": 2,
            "extra_class_category": 0,  # Category index
            "extra_class_size": 200,
            "extra_class_grade_min": 9,
            "extra_class_grade_max": 10,
            "extra_class_duration": 2,  # Number of timeslots
            "teacher_admin_idx": 0,  # This teacher is also an admin
            "extra_resource_type_name": "Projector",
            "extra_resource_value": "Foo",
        }
        self.setUpProgram(settings, extra_settings)
        self.setUpSchedule(settings, extra_settings)

    def setUpProgram(self, settings, extra_settings):
        # Initialize the program.
        super(ScheduleTest, self).setUp(**settings)
        # Create an extra timeslot.
        start_time = extra_settings["extra_timeslot_start"]
        end_time = start_time + datetime.timedelta(
                minutes=settings["timeslot_length"])
        Event.objects.get_or_create(
                program=self.program,
                event_type=self.event_type,
                start=start_time,
                end=end_time,
                short_description="Extra Slot",
                description=start_time.strftime("%H:%M %m/%d/%Y")
        )
        self.timeslots = self.program.getTimeSlots()

        # Create an extra room with the new resource
        res_type = ResourceType.get_or_create(
                extra_settings["extra_resource_type_name"])
        for i in extra_settings["extra_room_availability"]:
            room_capacity = extra_settings["extra_room_capacity"]
            room, created = Resource.objects.get_or_create(
                name="Extra Room",
                num_students=room_capacity,
                event=self.timeslots[i],
                res_type=ResourceType.get_or_create("Classroom"))
            Resource.objects.get_or_create(
                name="Extra Room Projector",
                event=self.timeslots[i],
                res_type=res_type,
                res_group=room.res_group,
                attribute_value=extra_settings["extra_resource_value"],)
        self.rooms = self.program.getClassrooms()

        # Create an extra class
        duration = (
            (settings["timeslot_length"]
                * extra_settings["extra_class_duration"])
            + (settings["timeslot_gap"]
                * (extra_settings["extra_class_duration"] - 1))
            ) / 60.0
        new_class, created = ClassSubject.objects.get_or_create(
                title="Extra Class",
                category=self.categories[
                    extra_settings["extra_class_category"]],
                grade_min=extra_settings["extra_class_grade_min"],
                grade_max=extra_settings["extra_class_grade_max"],
                parent_program=self.program,
                class_size_max=extra_settings["extra_class_size"],
                class_info="Extra Desctiption!",
                duration=duration)
        for i in extra_settings["extra_class_teachers"]:
            new_class.makeTeacher(self.teachers[i])
        for i in xrange(extra_settings["extra_class_sections"]):
            if new_class.get_sections().count() <= i:
                new_class.add_section(duration=duration)
        new_class.accept()
        # Add resource requests to the new sections.
        for section in new_class.get_sections():
            ResourceRequest.objects.get_or_create(
                target=section,
                target_subj=section.parent_class,
                res_type=res_type,
                desired_value=extra_settings["extra_resource_value"])

        # Set availabilities: each teacher is available except in the timeslot
        # sharing his index (e.g. teacher 0 isn't available in the 0th
        # timeslot)
        for i, t in enumerate(self.teachers):
            for j, ts in enumerate(self.timeslots):
                if i != j:
                    t.addAvailableTime(self.program, ts)

        self.teachers[
                extra_settings["teacher_admin_idx"]].makeRole("Administrator")

    def setUpSchedule(self, settings, extra_settings):
        # This creates the schedule we expect to see, reflecting the
        # combination of the implementation of ProgramFrameworkTest.setUp and
        # setUpProgram above.

        # Create timeslots
        timeslots = []
        for i in xrange(settings["num_timeslots"]):
            start_time = settings["start_time"] \
                + datetime.timedelta(minutes=(
                    i * (settings["timeslot_length"]
                         + settings["timeslot_gap"])))
            end_time = start_time + \
                datetime.timedelta(minutes=settings["timeslot_length"])
            timeslots.append(models.AS_Timeslot(
                start_time, end_time, i+1, None))
        start_time = extra_settings["extra_timeslot_start"]
        end_time = start_time + datetime.timedelta(
                minutes=settings["timeslot_length"])
        timeslots.append(models.AS_Timeslot(
            start_time, end_time, len(timeslots) + 1, None))

        # Create classrooms and furnishings
        classrooms = []
        for i in xrange(settings["num_rooms"]):
            classrooms.append(models.AS_Classroom(
                "Room {}".format(str(i)), timeslots[:-1], i + 1))
        restype_id = ResourceType.objects.get(
            name=extra_settings["extra_resource_type_name"]).id
        extra_resource_type = models.AS_ResourceType(
            extra_settings["extra_resource_type_name"],
            restype_id,
            extra_settings["extra_resource_value"])
        room_timeslots = [timeslots[i] for i in
                          extra_settings["extra_room_availability"]]
        classrooms.append(models.AS_Classroom(
                "Extra Room", room_timeslots, len(classrooms) + 1,
                {extra_resource_type.name: extra_resource_type}))
        classrooms_dict = {room.name: room for room in classrooms}

        # Create teachers
        teachers = []
        for i in xrange(settings["num_teachers"]):
            teacher_id = i + 1
            teacher_availability = [
                    ts for j, ts in enumerate(timeslots) if j != i]
            is_admin = (i == extra_settings["teacher_admin_idx"])
            teachers.append(models.AS_Teacher(
                teacher_availability, teacher_id, is_admin))
        teachers_dict = {teacher.id: teacher for teacher in teachers}

        # Create sections
        subject_count = 0
        section_id = 1
        sections = []
        for t in teachers:
            for i in xrange(settings["classes_per_teacher"]):
                category_id = 1 + (subject_count % settings["num_categories"])
                grade_min = 7
                grade_max = 12
                capacity = settings["room_capacity"]
                subject_count += 1
                duration = settings["timeslot_length"] / 60.0
                for j in xrange(settings["sections_per_class"]):
                    sections.append(models.AS_ClassSection(
                        [t], duration, capacity,
                        category_id, [],
                        section_id=section_id,
                        grade_min=grade_min, grade_max=grade_max))
                    section_id += 1
        category_id = extra_settings["extra_class_category"] + 1
        grade_min = extra_settings["extra_class_grade_min"]
        grade_max = extra_settings["extra_class_grade_max"]
        capacity = extra_settings["extra_class_size"]
        duration = (
            (settings["timeslot_length"]
                * extra_settings["extra_class_duration"])
            + (settings["timeslot_gap"]
                * (extra_settings["extra_class_duration"] - 1))
            ) / 60.0
        section_teachers = [
            t for i, t in enumerate(teachers)
            if i in extra_settings["extra_class_teachers"]]
        for i in xrange(extra_settings["extra_class_sections"]):
            sections.append(models.AS_ClassSection(
                section_teachers, duration, capacity,
                category_id, [],
                section_id=section_id,
                grade_min=grade_min, grade_max=grade_max))
            section_id += 1
        sections_dict = {section.id: section for section in sections}

        self.schedule = models.AS_Schedule(
            program=self.program, timeslots=timeslots,
            class_sections=sections_dict, teachers=teachers_dict,
            classrooms=classrooms_dict)

    def test_schedule_load(self):
        loaded_schedule = models.AS_Schedule.load_from_db(self.program)
        # TODO: check that the schedules match
