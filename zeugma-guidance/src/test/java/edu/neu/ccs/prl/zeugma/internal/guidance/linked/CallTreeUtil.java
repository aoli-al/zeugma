package edu.neu.ccs.prl.zeugma.internal.guidance.linked;

import edu.neu.ccs.prl.zeugma.examples.SimpleMapGenerator;
import edu.neu.ccs.prl.zeugma.examples.SimpleXmlGenerator;
import edu.neu.ccs.prl.zeugma.internal.guidance.FuzzTarget;
import edu.neu.ccs.prl.zeugma.internal.guidance.TestReport;
import edu.neu.ccs.prl.zeugma.internal.guidance.linked.CallTreeVertex;
import edu.neu.ccs.prl.zeugma.internal.guidance.linked.CallTreeVertexVisitor;
import edu.neu.ccs.prl.zeugma.internal.guidance.linked.MethodCallVertex;
import edu.neu.ccs.prl.zeugma.internal.guidance.linked.ParameterRequestVertex;
import edu.neu.ccs.prl.zeugma.internal.provider.PrimitiveWriter;
import edu.neu.ccs.prl.zeugma.internal.provider.RecordingDataProvider;
import edu.neu.ccs.prl.zeugma.internal.util.ByteList;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.function.Predicate;

public final class CallTreeUtil {
    private CallTreeUtil() {
        throw new AssertionError();
    }

    public static LinkedHashMap<String, Long> initialMap() {
        LinkedHashMap<String, Long> map = new LinkedHashMap<>();
        map.put("blue", 101L);
        map.put("red", -70L);
        return map;
    }

    public static void writeMap(ByteList list, Map<String, Long> map) {
        PrimitiveWriter.write(list, map.size());
        for (String key : map.keySet()) {
            int[] codePoints = key.codePoints().toArray();
            PrimitiveWriter.write(list, codePoints.length);
            for (int codePoint : codePoints) {
                PrimitiveWriter.write(list, codePoint);
            }
            PrimitiveWriter.write(list, map.get(key));
        }
    }

    public static List<CallTreeVertex> findMatches(CallTreeVertex vertex, Predicate<CallTreeVertex> predicate) {
        List<CallTreeVertex> matches = new ArrayList<>();
        vertex.preorderTraverse(new CallTreeVertexVisitor() {
            @Override
            public void visit(MethodCallVertex vertex) {
                if (predicate.test(vertex)) {
                    matches.add(vertex);
                }
            }

            @Override
            public void visit(ParameterRequestVertex vertex) {
                if (predicate.test(vertex)) {
                    matches.add(vertex);
                }
            }
        });
        return matches;
    }

    public static boolean isMethodCall(CallTreeVertex vertex, String methodName) {
        return vertex instanceof MethodCallVertex &&
                ((MethodCallVertex) vertex).getMethod().getName().equals(methodName);
    }

    public static GenerateFuzzTarget<Map<String, Long>> createMapTarget() {
        return new GenerateFuzzTarget<>(new SimpleMapGenerator()::generateMap);
    }

    public static GenerateFuzzTarget<String> createXmlTarget() {
        return new GenerateFuzzTarget<>(new SimpleXmlGenerator()::generateXml);
    }

    public static void writeBasicXml(ByteList input) {
        PrimitiveWriter.write(input, 'a'); // name
        PrimitiveWriter.write(input, 1); // number of attributes
        PrimitiveWriter.write(input, 'b'); // first attribute name
        PrimitiveWriter.write(input, 'c'); // first attribute value
        PrimitiveWriter.write(input, true); // add element children
        PrimitiveWriter.write(input, 2); // number of children
        PrimitiveWriter.write(input, 'y'); // first child name
        PrimitiveWriter.write(input, 0); // first child attributes
        PrimitiveWriter.write(input, false); // no element children
        PrimitiveWriter.write(input, false); // no text child
        PrimitiveWriter.write(input, 'x'); // second child name
        PrimitiveWriter.write(input, 0); // second child attributes
        PrimitiveWriter.write(input, false); // non-element vertex
        PrimitiveWriter.write(input, true); // add text child
        PrimitiveWriter.write(input, 'g'); // text value
    }

    public static void writeBasicMap(ByteList input) {
        writeMap(input, initialMap());
    }

    public static final class GenerateFuzzTarget<T> implements FuzzTarget {
        private final Function<? super RecordingDataProvider, T> generator;
        private T structure;

        public GenerateFuzzTarget(Function<? super RecordingDataProvider, T> generator) {
            this.generator = generator;
        }

        @Override
        public int getMaxTraceSize() {
            return 5;
        }

        @Override
        public int getMaxInputSize() {
            return Integer.MAX_VALUE;
        }

        @Override
        public String getDescriptor() {
            return getClass().getSimpleName();
        }

        @Override
        public TestReport run(RecordingDataProvider provider) {
            structure = generator.apply(provider);
            return new TestReport(null, provider.getRecording(), this, "", null);
        }

        public T getStructure() {
            return structure;
        }
    }
}
