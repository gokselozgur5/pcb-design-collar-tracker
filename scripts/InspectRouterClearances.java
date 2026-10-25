import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import app.freerouting.board.actions.ItemIdGenerator;
import app.freerouting.board.model.items.Item;
import app.freerouting.drc.ClearanceViolation;
import app.freerouting.io.BoardReadResult;
import app.freerouting.io.specctra.DsnReader;
import app.freerouting.settings.GlobalSettings;
import com.google.gson.GsonBuilder;

/** Inspect loaded geometry without routing, weakening rules or changing the DSN. */
public class InspectRouterClearances {
    static Object item(Item item) {
        var r = new LinkedHashMap<String, Object>();
        r.put("id", item.getId());
        r.put("type", item.getClass().getSimpleName());
        r.put("net", item.getAllNetNames());
        r.put("component", item.componentName());
        r.put("fixed", item.getFixedState().toString());
        r.put("clearance_class", item.clearanceClassIndex());
        r.put("bounds", item.boundingBox().toString());
        return r;
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("INPUT.dsn OUTPUT.json RUNTIME_DIR");
        if (Files.exists(Path.of(args[1]))) throw new IllegalArgumentException("Preserve earlier output");
        GlobalSettings.setUserDataPath(Path.of(args[2]).toAbsolutePath());
        BoardReadResult result;
        try (var stream = Files.newInputStream(Path.of(args[0]))) {
            result = DsnReader.readBoard(stream, null, new ItemIdGenerator());
        }
        if (!(result instanceof BoardReadResult.Success success)) throw new IllegalStateException(result.toString());
        var rows = new ArrayList<Object>();
        for (var v : ClearanceViolation.aggregateSortedBySeverity(success.board().getItems())) {
            var row = new LinkedHashMap<String, Object>();
            row.put("expected_board_units", v.expectedClearance);
            row.put("actual_board_units", v.actualClearance);
            row.put("layer", v.layer);
            row.put("category", v.getCategory().toString());
            row.put("first", item(v.firstItem));
            row.put("second", item(v.secondItem));
            rows.add(row);
        }
        Files.writeString(Path.of(args[1]), new GsonBuilder().setPrettyPrinting().create().toJson(rows) + "\n");
        System.out.println("Loaded clearance records: " + rows.size());
    }
}
