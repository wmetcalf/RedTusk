package io.redtusk.worker;

import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;

import java.util.Comparator;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/** Logical provenance paths; never interpreted as filesystem destinations. */
final class ResourcePaths {
    record Resource(String path, String parent, int depth) { }

    private ResourcePaths() { }

    /**
     * The one identity transformation for a resource name, shared by pass 1 (resolve) and
     * pass 2 (EmbeddedFileExtractor.SavingExtractor): backslashes become '/', leading '/' go.
     */
    static String normalizeName(String name) {
        return name.replace('\\', '/').replaceFirst("^/+", "");
    }

    static String captureKey(Metadata metadata) {
        String id = metadata.get(TikaCoreProperties.EMBEDDED_ID_PATH);
        return id == null ? metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH) : "id:" + id;
    }

    static Map<Metadata, Resource> resolve(List<Metadata> entries) {
        Map<Metadata, Resource> result = new IdentityHashMap<>();
        Map<String, Resource> byId = new HashMap<>();
        // RecursiveParserWrapper records children before their container finishes.
        // Its ID hierarchy, unlike a basename or directory name, identifies parents.
        var ordered = entries.stream().sorted(Comparator.comparingInt(m -> {
            String id = m.get(TikaCoreProperties.EMBEDDED_ID_PATH);
            return id == null ? 0 : (int) id.chars().filter(c -> c == '/').count();
        })).toList();
        for (Metadata metadata : ordered) {
            String raw = metadata.get(TikaCoreProperties.EMBEDDED_RESOURCE_PATH);
            String id = metadata.get(TikaCoreProperties.EMBEDDED_ID_PATH);
            if (raw == null || raw.isEmpty() || raw.equals("/")) {
                result.put(metadata, new Resource("/", null, 0));
                continue;
            }
            int parentSeparator = id == null ? -1 : id.lastIndexOf('/');
            Resource parent = parentSeparator <= 0 ? null : byId.get(id.substring(0, parentSeparator));
            String name = metadata.get(TikaCoreProperties.RESOURCE_NAME_KEY);
            if (name == null || name.isBlank()) name = metadata.get(TikaCoreProperties.INTERNAL_PATH);
            if (name == null || name.isBlank()) name = raw.substring(raw.lastIndexOf('/') + 1);
            name = normalizeName(name);
            String parentPath = parent == null ? "/" : parent.path();
            String path = (parentPath.equals("/") ? "" : parentPath) + "/" + name;
            Resource resource = new Resource(path, parentPath, parent == null ? 1 : parent.depth() + 1);
            result.put(metadata, resource);
            if (id != null) byId.put(id, resource);
        }
        return result;
    }
}
