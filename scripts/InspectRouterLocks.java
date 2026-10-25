import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.TreeMap;

import app.freerouting.board.actions.ItemIdGenerator;
import app.freerouting.board.model.items.Trace;
import app.freerouting.board.model.items.Via;
import app.freerouting.io.BoardReadResult;
import app.freerouting.io.specctra.DsnReader;
import app.freerouting.settings.GlobalSettings;
import com.google.gson.GsonBuilder;

/** Read the actual Freerouting 2.5.0 lock state without routing or changing the DSN. */
public class InspectRouterLocks {
    public static void main(String[] args) throws Exception {
        if (args.length != 3 && args.length != 4) {
            throw new IllegalArgumentException(
                "Usage: INPUT.dsn OUTPUT.json RUNTIME_DIR [--require-movable]");
        }
        if (args.length == 4 && !args[3].equals("--require-movable")) {
            throw new IllegalArgumentException("Unknown option: " + args[3]);
        }
        Path input = Path.of(args[0]);
        Path output = Path.of(args[1]);
        if (Files.exists(output)) {
            throw new IllegalArgumentException("Preserve earlier evidence; choose a new output");
        }
        GlobalSettings.setUserDataPath(Path.of(args[2]).toAbsolutePath());
        BoardReadResult result;
        try (var stream = Files.newInputStream(input)) {
            result = DsnReader.readBoard(stream, null, new ItemIdGenerator());
        }
        if (!(result instanceof BoardReadResult.Success success)) {
            throw new IllegalStateException(result.toString());
        }
        var totals = new TreeMap<String, Integer>();
        var nets = new TreeMap<String, TreeMap<String, Integer>>();
        for (var item : success.board().getItems()) {
            if (!(item instanceof Trace) && !(item instanceof Via)) {
                continue;
            }
            String state = item.getFixedState().toString();
            totals.merge(state, 1, Integer::sum);
            nets.computeIfAbsent(item.getAllNetNames(), key -> new TreeMap<>())
                .merge(state, 1, Integer::sum);
        }
        boolean movable = totals.getOrDefault("USER_FIXED", 0) == 0
            && totals.getOrDefault("UNFIXED", 0) > 0;
        var report = new LinkedHashMap<String, Object>();
        report.put("input", args[0]);
        report.put("input_sha256", HexFormat.of().formatHex(
            MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(input))));
        report.put("totals", totals);
        report.put("nets", nets);
        report.put("movable_without_user_fixed_items", movable);
        report.put("scope", "Loaded router lock states only. Movable segments may be merged "
            + "into polylines. This does not establish native connectivity or DRC acceptance.");
        Files.writeString(output, new GsonBuilder().setPrettyPrinting().create().toJson(report) + "\n");
        System.out.println(totals);
        if (args.length == 4 && !movable) {
            throw new IllegalStateException("Unexpected fixed signal items or no movable routing");
        }
    }
}
