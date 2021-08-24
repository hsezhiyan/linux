#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>

MODULE_DESCRIPTION("List current processes");
MODULE_AUTHOR("Kernel Hacker");
MODULE_LICENSE("GPL");

static void print_pid_and_comm(struct task_struct *p) {
	pr_info("PID: %d, executable name: %s", p->pid, p->comm);
}

static int my_proc_init(void)
{
	struct task_struct *p;	
	print_pid_and_comm(current);
	for_each_process(p) {
		print_pid_and_comm(p);
	}

	return 0;
}

static void my_proc_exit(void)
{
	print_pid_and_comm(current);

}

module_init(my_proc_init);
module_exit(my_proc_exit);
