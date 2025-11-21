package UseDB;

import Entities.StudyHours;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

public class Writer {
    private Connection conn;
    public Writer(Connection conn){
        this.conn = conn;
    }

    public int addFaculty(String facultyName){
        String sql = "insert into faculty(faculty_name) values (?)";
        try(PreparedStatement pr = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)){
            pr.setString(1,facultyName);
            pr.executeUpdate();
            ResultSet key = pr.getGeneratedKeys();
            key.next();
            return key.getInt(1);
        } catch (Exception e) {
            System.out.println("already exist!");
            return 0;
        }
    }

    public int addSpec(String specName, Integer faculty_id, Integer yearsOfStudy){
        String sql = "INSERT INTO Specialization (spec_name, faculty_id, years_of_study) " +
                "VALUES (?,?,?)";
        try(PreparedStatement pr = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS))
        {
            pr.setString(1,specName);
            pr.setInt(2,faculty_id);
            pr.setInt(3,yearsOfStudy);
            pr.executeUpdate();
            ResultSet key = pr.getGeneratedKeys();
            key.next();
            return key.getInt(1);
        } catch (Exception e) {
            System.out.println("already exist!");
            return 0;
        }
    }


    public int addGroup(Integer specId, String name){
        String sql = "insert into students_group(group_name, spec_id) values (?,?)";
        try(PreparedStatement pr = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)){
            pr.setString(1,name);
            pr.setInt(2,specId);
            pr.executeUpdate();
            ResultSet key = pr.getGeneratedKeys();
            key.next();
            return key.getInt(1);
        } catch (Exception e) {
            System.out.println("already exist!");
            return 0;
        }
    }

    public int addDiscipline(Integer specId, String name, Integer studySemester, Float credits){
        String sql = "insert into discipline(discipline_name, study_semester, credits, spec_id) values (?,?,?,?)";

        try(PreparedStatement pr = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS))
        {
            pr.setString(1,name);
            pr.setInt(2,studySemester);
            pr.setFloat(3,credits);
            pr.setInt(4,specId);
            pr.executeUpdate();
            ResultSet key = pr.getGeneratedKeys();
            key.next();
            return key.getInt(1);
        } catch (Exception e) {
            System.out.println("already exist!");
            return 0;
        }
    }

    public int addStudyHoursForDiscipline(StudyHours studyHours){
        String detailsSql = "insert into study_hours(discipline_id, contact_study_hours, independent_study_hours, course_hours, seminar_hours,laboratories_hours) values (?,?,?,?,?,?)";
        try(PreparedStatement detailPr = conn.prepareStatement(detailsSql, Statement.RETURN_GENERATED_KEYS)){
            detailPr.setInt(1, studyHours.disciplineId());
            detailPr.setFloat(2,studyHours.contactStudyHours());
            detailPr.setFloat(3,studyHours.independentStudyHours());
            detailPr.setFloat(4,studyHours.courseHours());
            detailPr.setFloat(5, studyHours.seminarHours());
            detailPr.setFloat(6,studyHours.laboratoriesHours());
            detailPr.executeUpdate();
            ResultSet key = detailPr.getGeneratedKeys();
            key.next();
            return key.getInt(1);
        } catch (Exception e) {
            System.out.println("already exist!");
            return 0;
        }
    }

}
