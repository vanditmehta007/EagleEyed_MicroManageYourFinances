import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import {
    ArrowRight,
    Zap,
    Shield,
    Brain,
    MessageSquare,
    Scan,
    Users,
    ChevronRight,
    Briefcase,
    CheckCircle2
} from 'lucide-react';

const LandingPage: React.FC = () => {
    const features = [
        {
            icon: <Brain className="w-6 h-6 text-primary" />,
            title: "AI-Powered Analysis",
            description: "Instantly extract insights from your documents with our advanced AI models. No more manual data entry."
        },
        {
            icon: <Scan className="w-6 h-6 text-primary" />,
            title: "Smart Scanning",
            description: "Turn physical documents into digital data with high-precision OCR and automated formatting."
        },
        {
            icon: <Shield className="w-6 h-6 text-primary" />,
            title: "Secure Sharing",
            description: "Share sensitive documents with clients and team members securely with granular permission controls."
        },
        {
            icon: <MessageSquare className="w-6 h-6 text-primary" />,
            title: "Real-time Chat",
            description: "Ask questions about your documents and get immediate answers through our intelligent chat assistant."
        },
        {
            icon: <Users className="w-6 h-6 text-primary" />,
            title: "Client Management",
            description: "Organize client data, documents, and interactions in one centralized, easy-to-use dashboard."
        },
        {
            icon: <Zap className="w-6 h-6 text-primary" />,
            title: "Automated Workflows",
            description: "Streamline your document processing pipeline with custom workflows and automated triggers."
        }
    ];

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
                <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                            <Scan className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">Eagle Eyed</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link to="/login">
                            <Button variant="ghost" className="text-sm font-medium hover:bg-white/5">
                                Log in
                            </Button>
                        </Link>
                        <Link to="/signup">
                            <Button className="text-sm font-medium bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/20">
                                Sign up
                            </Button>
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-primary/20 blur-[120px] rounded-full opacity-50" />
                </div>

                <div className="container mx-auto px-6 text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        {/* <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-8">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                            </span>
                            <span className="text-sm font-medium text-muted-foreground">v2.0 is now live</span> 
                            <ChevronRight className="w-3 h-3 text-muted-foreground" />
                        </div> */}

                        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-8 bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/70">
                            The Ultimate CA - Client <br /> Document Workflow
                        </h1>

                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed">
                            Eagle Eyed streamlines collaboration between Chartered Accountants and Clients with powerful AI analysis,
                            secure sharing, and automated data extraction.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                            <Link to="/signup">
                                <Button size="lg" className="h-12 px-8 text-base bg-primary hover:bg-primary/90 text-white shadow-xl shadow-primary/20 transition-all hover:scale-105">
                                    Get Started <ArrowRight className="ml-2 w-4 h-4" />
                                </Button>
                            </Link>
                            <Link to="/login">
                                <Button size="lg" variant="outline" className="h-12 px-8 text-base hover:bg-white/5 backdrop-blur-sm">
                                    View Demo
                                </Button>
                            </Link>
                        </div>
                    </motion.div>

                    {/* Interactive Role Cards */}
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.7, delay: 0.2 }}
                        className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto px-4"
                    >
                        {/* CA Card */}
                        <motion.div
                            whileHover={{ y: -10 }}
                            className="p-8 rounded-2xl border border-blue-500/20 bg-blue-500/5 backdrop-blur-sm hover:bg-blue-500/10 transition-colors text-left"
                        >
                            <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center mb-6">
                                <Briefcase className="w-6 h-6 text-blue-500" />
                            </div>
                            <h3 className="text-xl font-bold mb-4">Chartered Accountant</h3>
                            <ul className="space-y-3">
                                {["Client Management", "Document Review", "Compliance Tracking", "Secure Sharing", "AI Companion: Helps with queries & improves work"].map((item, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm text-muted-foreground">
                                        <CheckCircle2 className="w-4 h-4 text-blue-500" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </motion.div>

                        {/* Client Card */}
                        <motion.div
                            whileHover={{ y: -10 }}
                            className="p-8 rounded-2xl border border-green-500/20 bg-green-500/5 backdrop-blur-sm hover:bg-green-500/10 transition-colors text-left"
                        >
                            <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center mb-6">
                                <Users className="w-6 h-6 text-green-500" />
                            </div>
                            <h3 className="text-xl font-bold mb-4">Client</h3>
                            <ul className="space-y-3">
                                {["Document Upload", "Status Tracking", "Secure Storage", "Easy Communication", "AI Companion: Investment tips & upload help"].map((item, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm text-muted-foreground">
                                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </motion.div>

                        {/* AI Card */}
                        <motion.div
                            whileHover={{ y: -10 }}
                            className="p-8 rounded-2xl border border-purple-500/20 bg-purple-500/5 backdrop-blur-sm hover:bg-purple-500/10 transition-colors text-left"
                        >
                            <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center mb-6">
                                <Brain className="w-6 h-6 text-purple-500" />
                            </div>
                            <h3 className="text-xl font-bold mb-4">Artificial Intelligence</h3>
                            <ul className="space-y-3">
                                {["Automated Extraction", "Smart Analysis", "Instant Insights", "Error Detection", "Transaction Querying: Search transactions instantly"].map((item, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm text-muted-foreground">
                                        <CheckCircle2 className="w-4 h-4 text-purple-500" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </motion.div>
                    </motion.div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-24 bg-muted/30 relative">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything you need</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                            Powerful features designed to help you manage, analyze, and share documents with ease.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {features.map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: index * 0.1 }}
                                viewport={{ once: true }}
                                className="group p-6 rounded-2xl bg-background border border-border/50 hover:border-primary/50 transition-colors hover:shadow-lg hover:shadow-primary/5"
                            >
                                <div className="mb-4 p-3 rounded-xl bg-primary/10 w-fit group-hover:bg-primary/20 transition-colors">
                                    {feature.icon}
                                </div>
                                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                                <p className="text-muted-foreground leading-relaxed">
                                    {feature.description}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-24 relative overflow-hidden">
                <div className="container mx-auto px-6 text-center relative z-10">
                    <h2 className="text-4xl md:text-5xl font-bold mb-8 tracking-tight">
                        Ready to streamline your workflow?
                    </h2>
                    {/* <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            Join thousands of teams who trust Eagle Eyed for their document management needs.
          </p> */}
                    <Link to="/signup">
                        <Button size="lg" className="h-14 px-10 text-lg bg-primary hover:bg-primary/90 text-white shadow-2xl shadow-primary/30 rounded-full">
                            Start for free
                        </Button>
                    </Link>
                </div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 blur-[100px] rounded-full -z-10" />
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-border/50 bg-background">
                <div className="container mx-auto px-6">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-8">
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center">
                                <Scan className="w-4 h-4 text-white" />
                            </div>
                            <span className="font-bold text-lg">Eagle Eyed</span>
                        </div>
                        <div className="flex gap-8 text-sm text-muted-foreground">
                            <a href="#" className="hover:text-primary transition-colors">Features</a>
                            <a href="#" className="hover:text-primary transition-colors">Pricing</a>
                            <a href="#" className="hover:text-primary transition-colors">About</a>
                            <a href="#" className="hover:text-primary transition-colors">Contact</a>
                        </div>
                        <div className="text-sm text-muted-foreground">
                            © 2025 Eagle Eyed. All rights reserved.
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
