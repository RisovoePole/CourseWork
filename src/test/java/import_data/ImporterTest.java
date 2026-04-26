package import_data;

import entities.Faculty;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Vector;

import static org.junit.jupiter.api.Assertions.*;

class ImporterTest {

    @Test
    void setPathTest() {
        Importer importer = new Importer();
        Path path = Paths.get("test.txt");

        importer.setPath(path);

        assertEquals(path, importer.getPath());
    }

    @Test
    void getPathTest(){
        Importer importer = new Importer();
        Path expectedPath = Paths.get("test.txt");

        importer.setPath(expectedPath);

        Path actualPath = importer.getPath();

        assertEquals(expectedPath,actualPath);
    }

    @Test
    void setGetSeparatorTest(){
        Importer importer = new Importer();
        Character expectedSeparator = ';';

        importer.setSeparator(expectedSeparator);

        Character actualSeparator = importer.getSeparator();

        assertEquals(expectedSeparator, actualSeparator);
    }


//    @Test
//    void findCorrespondIndexesTest(){
//        Importer importer = new Importer();
//        String[] testHeaders= {"N","f_name", "l_name", "age"};
//        String[] correctHeaders = {"f_name","l_name"};
//        Integer[] expectedCorrespondIndexes = {1,2};
//
//        Integer[] actualCorrespondIndexes = importer.findCorrespondIndexes(testHeaders,correctHeaders);
//
//        assertArrayEquals(expectedCorrespondIndexes,actualCorrespondIndexes);
//    }

    @Test
    void importFacultiesTest1(){
        Importer importer= new Importer();
        Vector<Faculty> expected = new Vector<>( List.of(
                new Faculty(null, "Math"),
                new Faculty(null, "NeMath")
        ));
         Vector<Faculty> actual = assertDoesNotThrow(
                ()->importer.importFaculties(Paths.get("src","test","Files", "Faculties","test.csv"))
        );

         assertArrayEquals(expected.toArray(),actual.toArray());
    }

    @Test
    void importFacultiesTest2(){
        Importer importer= new Importer();
        Vector<Faculty> expected = new Vector<>( List.of(
                new Faculty(null, "Math"),
                new Faculty(null, "")
        ));
        Vector<Faculty> actual = assertDoesNotThrow(
                ()->importer.importFaculties(Paths.get("src","test","Files", "Faculties","test2.csv"))
        );

        assertArrayEquals(expected.toArray(),actual.toArray());
    }

    @Test
    void importFacultiesTest3(){
        Importer importer= new Importer();
        ImportException ex = assertThrows(
                ImportException.class,
                ()->importer.importFaculties(Paths.get("src","test","Files", "Faculties","test3.csv"))
        );

        assertEquals("Not enough data on line 3",ex.getMessage());

    }
}
