package Entities;

public record Discipline(Integer id,
                         String name,
                         Integer studySemester,
                         Integer requiredRoomTypeId,
                         Float credits,
                         Integer specId) {
}
