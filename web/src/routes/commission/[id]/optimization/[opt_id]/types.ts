import type {Readable} from "svelte/store";
import type {OptimizationConfiguration, SolutionCommission} from "../optimization_types";

export type PossibleOptimizationStatuses = 'running' | 'ended' | 'not_started';

export type OptimizationStatus = Readable<{
    running: boolean,
    configurationLocked: boolean,
    solutions: { all: SolutionCommission[]; afternoon: SolutionCommission[]; morning: SolutionCommission[] },
    status: PossibleOptimizationStatuses
}>;

export function getOptimizationStatus(conf: OptimizationConfiguration | undefined) {
    let status: PossibleOptimizationStatuses = 'not_started';

    if (!conf)
        return {
            configurationLocked: false,
            running: false,
            solutions: {
                all: [],
                morning: [],
                afternoon: []
            },
            status
        };

    let solutions = conf.solution_commissions;

    if (conf.run_lock) {
        if (conf.execution_details.length > 0) {
            status = 'ended';
        } else {
            status = 'running';
        }
    }

    return {
        configurationLocked: conf.run_lock,
        /*
        * The list isn't used outside the first element, it has been implemented this way to be able to hold
        * multiple logs if necessary for further functionalities.
        */
        running: conf.execution_details.length > 0,
        solutions: {
            all: solutions,
            morning: solutions.filter(s => s.morning),
            afternoon: solutions.filter(s => !s.morning)
        },
        status
    };
}