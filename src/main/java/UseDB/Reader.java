package UseDB;

import Entities.*;

import java.sql.*;
import java.util.*;

public class Reader {
    private Connection conn;

    public Reader(Connection conn) {
        this.conn = conn;
    }

    public Vector<Faculty> getFacultyList() {
        String sql = "Select * from faculty";
        try (PreparedStatement pr = conn.prepareStatement(sql)) {
            Vector<Faculty> arr = new Vector<>();
            ResultSet rs = pr.executeQuery();
            while (rs.next()) {
                Faculty f = new Faculty(
                        rs.getInt(1),
                        rs.getString(2)
                );
                arr.add(f);
            }
            return arr;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public Vector<Specialization> getSpecsByFaculty(Integer facultyId) {
        String sql = "select spec_id, spec_name, faculty_id, years_of_study from specialization " +
                "where faculty_id = ?";
        try (PreparedStatement pr = conn.prepareStatement(sql)) {
            pr.setInt(1, facultyId);
            Vector<Specialization> arr = new Vector<>();
            ResultSet rs = pr.executeQuery();
            while (rs.next()) {
                Specialization f = new Specialization(
                        rs.getInt(1),
                        rs.getString(2),
                        rs.getInt(3),
                        rs.getInt(4)
                );
                arr.add(f);
            }
            return arr;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public Vector<Discipline> getDisciplinesBySpec(Integer SpecId) {
        String sql = "select discipline_id, discipline_name, study_semester, required_room_type, credits, spec_id " +
                "from discipline " +
                "where spec_id = ?";
        try (PreparedStatement pr = conn.prepareStatement(sql)) {
            pr.setInt(1, SpecId);
            Vector<Discipline> arr = new Vector<>();
            ResultSet rs = pr.executeQuery();
            while (rs.next()) {
                Discipline f = new Discipline(
                        rs.getInt(1),
                        rs.getString(2),
                        rs.getInt(3),
                        rs.getInt(4),
                        rs.getFloat(5),
                        rs.getInt(6)
                );
                arr.add(f);
            }
            return arr;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public Vector<StudentGroup> getGroupsBySpec(Integer specId) {
        String sql = "select students_group_id, group_name, professor_inspector, spec_id " +
                "from students_group " +
                "where spec_id = ?";
        try (PreparedStatement pr = conn.prepareStatement(sql)) {
            pr.setInt(1, specId);
            Vector<StudentGroup> arr = new Vector<>();
            ResultSet rs = pr.executeQuery();
            while (rs.next()) {
                StudentGroup f = new StudentGroup(
                        rs.getInt(1),
                        rs.getString(2),
                        rs.getInt(3),
                        rs.getInt(4)
                );
                arr.add(f);
            }
            return arr;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public StudyHours getStudyHoursByDiscipline(Integer disciplineId) {
        String sql = "select * from study_hours where discipline_id = ?";
        try (PreparedStatement pr = conn.prepareStatement(sql)) {
            pr.setInt(1, disciplineId);
            StudyHours studyHours;
            ResultSet rs = pr.executeQuery();
            if (rs.next()) {
                return new StudyHours(
                        rs.getInt(1),
                        rs.getFloat(2),
                        rs.getFloat(3),
                        rs.getFloat(4),
                        rs.getFloat(5),
                        rs.getFloat(6)
                );
            }
            return null;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
