package entities;

public record StudyHours(Integer disciplineId,
                         Float contactStudyHours,
                         Float independentStudyHours,
                         Float courseHours,
                         Float seminarHours,
                         Float laboratoriesHours) {

}
