"use client";

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { ChevronLeft, ChevronRight, Loader2, Link as LinkIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Slide {
  id: number;
  order_index: number;
  text_content: string | null;
  image_url: string | null;
}

interface Article {
  id: number;
  title: string;
  summary: string;
  url: string;
  slides: Slide[];
}

export function PreviewModal({ 
  projectId, 
  open, 
  onOpenChange 
}: { 
  projectId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [currentArticleIndex, setCurrentArticleIndex] = useState(0);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);

  useEffect(() => {
    if (open) {
      setLoading(true);
      apiClient.get(`/projects/${projectId}/preview`)
        .then(res => {
          setArticles(res.data.articles || []);
          setCurrentArticleIndex(0);
          setCurrentSlideIndex(0);
        })
        .finally(() => setLoading(false));
    }
  }, [open, projectId]);

  const currentArticle = articles[currentArticleIndex];
  const currentSlide = currentArticle?.slides?.[currentSlideIndex];

  const nextSlide = () => {
    if (currentSlideIndex < (currentArticle?.slides?.length || 0) - 1) {
      setCurrentSlideIndex(prev => prev + 1);
    } else if (currentArticleIndex < articles.length - 1) {
      setCurrentArticleIndex(prev => prev + 1);
      setCurrentSlideIndex(0);
    }
  };

  const prevSlide = () => {
    if (currentSlideIndex > 0) {
      setCurrentSlideIndex(prev => prev - 1);
    } else if (currentArticleIndex > 0) {
      setCurrentArticleIndex(prev => prev - 1);
      setCurrentSlideIndex((articles[currentArticleIndex - 1]?.slides?.length || 1) - 1);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Generated Content Preview</DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : articles.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-8 text-center border-2 border-dashed rounded-xl m-4 bg-muted/20">
            <Loader2 className="w-8 h-8 animate-spin mb-4 opacity-20" />
            <h3 className="text-lg font-medium text-foreground mb-1">No articles found</h3>
            <p>The workflow is either still running or hasn't started yet.</p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-lg line-clamp-1 flex-1">
                {currentArticle?.title}
              </h3>
              <a href={currentArticle?.url} target="_blank" rel="noopener noreferrer" className="ml-4 text-primary hover:underline flex items-center text-sm">
                <LinkIcon className="w-4 h-4 mr-1" /> Original Source
              </a>
            </div>

            <div className="flex-1 bg-muted/30 rounded-xl border flex items-center justify-center relative overflow-hidden p-6">
              {currentSlide ? (
                <div className="flex flex-col items-center max-w-2xl text-center space-y-6">
                  {currentSlide.image_url && (
                    <img src={currentSlide.image_url} alt="Slide visual" className="max-h-64 rounded-xl shadow-md object-cover" />
                  )}
                  <p className="text-xl md:text-2xl font-heading leading-relaxed">
                    {currentSlide.text_content}
                  </p>
                </div>
              ) : (
                <p className="text-muted-foreground">No slides available for this article.</p>
              )}

              {/* Navigation Arrows */}
              <div className="absolute inset-y-0 left-0 flex items-center px-4">
                <Button variant="secondary" size="icon" className="rounded-full shadow-lg h-12 w-12" onClick={prevSlide} disabled={currentArticleIndex === 0 && currentSlideIndex === 0}>
                  <ChevronLeft className="w-6 h-6" />
                </Button>
              </div>
              <div className="absolute inset-y-0 right-0 flex items-center px-4">
                <Button variant="secondary" size="icon" className="rounded-full shadow-lg h-12 w-12" onClick={nextSlide} disabled={currentArticleIndex === articles.length - 1 && currentSlideIndex === (currentArticle?.slides?.length || 1) - 1}>
                  <ChevronRight className="w-6 h-6" />
                </Button>
              </div>
            </div>

            <div className="mt-4 flex justify-between items-center text-sm text-muted-foreground">
              <span>Article {currentArticleIndex + 1} of {articles.length}</span>
              <div className="flex space-x-1">
                {currentArticle?.slides?.map((_, idx) => (
                  <div key={idx} className={`w-2 h-2 rounded-full ${idx === currentSlideIndex ? 'bg-primary' : 'bg-border'}`} />
                ))}
              </div>
              <span>Slide {currentSlideIndex + 1} of {currentArticle?.slides?.length || 0}</span>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
