/*
 * Based on JQF's CompilerTest which is available at:
 * https://github.com/rohanpadhye/JQF/blob/master/examples/src/test/java/edu/berkeley/cs/jqf/examples/closure
 * /CompilerTest.java
 *
 * CompilerTest is licensed under the following terms:
 *
 * Copyright (c) 2017-2018 The Regents of the University of California
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 * 1. Redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package edu.neu.ccs.prl.zeugma.eval;

import com.google.javascript.jscomp.Compiler;
import com.google.javascript.jscomp.*;
import com.pholser.junit.quickcheck.From;
import de.hub.se.jqf.examples.js.SplitJavaScriptCodeGenerator;
import edu.berkeley.cs.jqf.fuzz.Fuzz;
import edu.berkeley.cs.jqf.fuzz.JQF;
import edu.neu.ccs.prl.zeugma.generators.JavaScriptCodeGenerator;
import org.junit.Assume;
import org.junit.runner.RunWith;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.logging.LogManager;

@RunWith(JQF.class)
public class FuzzClosure {
    static {
        // Disable all logging by Closure passes
        LogManager.getLogManager().reset();
    }

    @Fuzz
    public void testWithInputStream(InputStream in) throws IOException {
        Compiler compiler = new Compiler(new PrintStream(new ByteArrayOutputStream(), false));
        CompilerOptions options = new CompilerOptions();
        compiler.disableThreads();
        options.setPrintConfig(false);
        CompilationLevel.SIMPLE_OPTIMIZATIONS.setOptionsForCompilationLevel(options);
        SourceFile input = SourceFile.fromCode("input", readStream(in));
        Result result = compiler.compile(SourceFile.fromCode("externs", ""), input, options);
        Assume.assumeTrue(result.success);
    }

    @Fuzz
    public void testWithGenerator(@From(JavaScriptCodeGenerator.class) String s) throws IOException {
        testWithInputStream(new ByteArrayInputStream(s.getBytes(StandardCharsets.UTF_8)));
    }

    @Fuzz
    public void testWithSplitGenerator(@From(SplitJavaScriptCodeGenerator.class) String s) throws IOException {
        testWithInputStream(new ByteArrayInputStream(s.getBytes(StandardCharsets.UTF_8)));
    }

    static String readStream(InputStream in) throws IOException {
        in = new BufferedInputStream(in);
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        for (int result = in.read(); result != -1; result = in.read()) {
            buffer.write((byte) result);
        }
        return buffer.toString(StandardCharsets.UTF_8.name());
    }
}
