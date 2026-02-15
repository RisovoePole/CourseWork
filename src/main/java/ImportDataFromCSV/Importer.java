package ImportDataFromCSV;

import Entities.Discipline;
import Entities.Faculty;
import UseDB.Writer;
import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.exceptions.CsvValidationException;

import java.io.*;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.Vector;

public class Importer {
    public Importer(){};

    private Path path = Paths.get(System.getProperty("user.dir"));

    public Path getPath() {
        return path;
    }

    public void setPath(Path path) {
        this.path = path;
    }

    private Integer[] findCorrespondIndexes(String[] headersFromCSV, String[] correctHeaders) throws ImportException{
        int rightHeadersLength = correctHeaders.length;
        Integer[] result = new Integer[rightHeadersLength];
        Map<String, Integer> headerIndexes = new HashMap<>();
        for(int idx = 0; idx<headersFromCSV.length; idx++){
            headerIndexes.put(headersFromCSV[idx].toLowerCase(), idx);
        }

        Vector<String> missingColumns = new Vector<>();

        for(int i=0; i<rightHeadersLength; i++){
            Integer index = headerIndexes.get(correctHeaders[i].toLowerCase());
            if(index == null) missingColumns.add(correctHeaders[i]);
            result[i] = index;
        }

        if(!missingColumns.isEmpty()) {
            StringBuilder errorMsg = new StringBuilder("ERROR: No column(s): ");
            errorMsg.append(String.join(", ", missingColumns));
            throw new ImportException(errorMsg.toString());
        }
        return result;
    }

    public Vector<Faculty> importFaculties(Path csvFilePath) throws ImportException, CsvValidationException, IOException {
        CSVReader reader = new CSVReader(new FileReader(csvFilePath.toFile()));
        String[] columnsNames = {"faculty name"};
        Integer[] rightIdx = new Integer[1];

        String[] nextLine, headers;
        if ((nextLine = reader.readNext()) != null) {
            headers = nextLine;
            rightIdx = findCorrespondIndexes(headers, columnsNames);
        } else {
            System.out.println("CSV file is empty");
            return null;
        }

        Vector<Faculty> facultyList = new Vector<>();

        while ((nextLine = reader.readNext()) != null) {
            String name = nextLine[rightIdx[0]];
            facultyList.add(new Faculty(null, name));
        }

        reader.close();
        return facultyList;
    }


//    public Vector<Discipline> importDisciplines(String csvFileName) {
//        try (CSVReader reader = new CSVReader(new FileReader(csvFileName))) {
//            String[] nextLine, headers;
//            if ((nextLine = reader.readNext()) != null) {
//                headers = nextLine;
//            } else {
//                System.out.println("CSV file is empty");
//                return null;
//            }
//
//            while ((nextLine = reader.readNext()) != null) {
//
//            }
//        } catch (IOException | CsvValidationException e) {
//            System.out.println(e.getMessage());
//            return null;
//        }
//    }

}
