package edu.neu.ccs.prl.zeugma.internal.fuzz;

import edu.neu.ccs.prl.zeugma.internal.guidance.FuzzTarget;
import edu.neu.ccs.prl.zeugma.internal.guidance.TestReport;
import edu.neu.ccs.prl.zeugma.internal.runtime.model.ModelRegistry;
import edu.neu.ccs.prl.zeugma.internal.util.ExtensibleMean;

import java.io.File;
import java.io.IOException;

public class GuidanceManager implements CampaignStatus {
    private final CampaignOutput out;
    private final CoverageCounter counter;
    private final FailureRegistry failureRegistry;
    /**
     * Tracks the amount of time remaining in the campaign.
     * <p>
     * Non-null.
     */
    private final Timer timer;
    /**
     * Mean size of executed inputs.
     * <p>
     * Non-null.
     */
    private final ExtensibleMean meanInputSize = new ExtensibleMean();

    public GuidanceManager(FuzzTarget target, File outputDirectory, long duration) throws IOException {
        this.out = new CampaignOutput(outputDirectory);
        this.counter = new CoverageCounter();
        this.failureRegistry = new FailureRegistry(target.getMaxTraceSize());
        this.timer = new Timer(duration).attach(new StatisticsRecorder(out, this),
                        StatisticsRecorder.calculateRecordPeriod(duration))
                .attach(new StatusScreen(target.getDescriptor(), duration, this), StatusScreen.calculateRecordPeriod());
    }

    public void finishedExecution(TestReport report, boolean[][] coverageMap, String mutationLog) throws IOException {
        if (report.getFailure() != null && failureRegistry.add(report.getFailure())) {
            out.saveToFailures(report.getRecording());
        }
        if (counter.update(coverageMap)) {
            out.saveToCorpus(report.getRecording());
        }
        if (!mutationLog.isEmpty()) {
            out.writeMutationLog(mutationLog);
        }
        meanInputSize.extend(report.getRecording().size());
    }

    public boolean unexpired() throws IOException {
        return timer.unexpired();
    }

    @Override
    public long getNumberOfRegisteredProbes() {
        return ModelRegistry.getNumberOfRegisteredProbes();
    }

    @Override
    public long getNumberOfCoveredProbes() {
        return counter.getNumberOfCoveredProbes();
    }

    @Override
    public long getCorpusSize() {
        return out.getCorpusSize();
    }

    @Override
    public long getNumberOfSavedFailures() {
        return out.getFailuresSize();
    }

    @Override
    public long getNumberOfExecutions() {
        return meanInputSize.size();
    }

    @Override
    public double getMeanInputSize() {
        return meanInputSize.orElse(0);
    }
}