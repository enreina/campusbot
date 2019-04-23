import firestoreClient as FirestoreClient

class Course(object):

    @staticmethod
    def find_course_by_name(courseName):
        courses = FirestoreClient.getDocuments('courses', [('nameLower', '==', courseName.lower())], withRef=True)
        if not courses:
            return None

        return courses[0].toDict()

    @staticmethod
    def find_or_create_course_ref(courseCode, courseName):
        # find by course code
        course = None
        if courseCode:
            course = FirestoreClient.getDocument('courses', courseCode.lower(), withRef=True)
        
        if course:
            return course['_ref']

        if not course:
            if not courseCode:
                courseCode = ""
                courseId = None
            else:
                courseCode = courseCode.upper()
                courseId = courseCode.lower()

            courseData = {
                'code': courseCode,
                'name': courseName,
                'nameLower': courseName.lower()
            }

        return FirestoreClient.createDocument('courses', documentId=courseId, data=courseData)

