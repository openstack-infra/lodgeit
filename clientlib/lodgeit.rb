#
# lodgeit.rb
#
# Copyright (C) 2006  Armin Ronacher
#
# Author: Armin Ronacher
# License: GNU GPL

require 'xmlrpc/client'


# == LodgeIt API
#
# This class provides access to the lodge it pastebin
# at http://paste.pocoo.org/
#
# == Examples
#
# === Basic Queries
#
# Example #1: Create LodgeIt instance
#
#     require 'lodgeit'
#     a = LodgeIt.new
#
# Example #2: Query LodgeIt
#
#     puts a.paste_count
#     puts a.private_count
#
# The latter should output the total count of pastes in the
# lodgeit pastebin, the latter the number of private pastes.
class LodgeIt

  PASTEBIN_URL = 'http://paste.pocoo.org/'
  SERVICE_URL = "#{PASTEBIN_URL}xmlrpc/"

  def initialize
    @service = XMLRPC::Client.new2(SERVICE_URL)
    @_languages = nil
  end

  def inspect
    '#<LodgeIt>'
  end

  # Number of pastes
  def paste_count
    @service.call('pastes.countPastes')
  end

  # number of private pastes
  def private_count
    @service.call('pastes.countPrivate')
  end

  # number of public pastes
  def public_count
    @service.call('pastes.countPublic')
  end

  # hash of supported languages
  def languages
    if @_languages.nil?
      h = Hash.new
      @service.call('pastes.getLanguages').each do |key, value|
        h[key.to_sym] = value
      end
      @_languages = h
    end
    @_languages
  end

  # this method checks if a language exists
  def language_exists? alias_
    rv = self.get_name_by_alias(alias_.to_s)
    not rv.nil?
  end

  # get the alias for a filename
  def get_alias_for_filename filename
    rv = @service.call('pastes.getAliasForFilename', filename)
    (rv.empty?) ? nil : rv
  end

  # get the alias for a mimetype
  def get_alias_for_mimetype mimetype
    rv = @service.call('pastes.getAliasForMimetype', mimetype)
    (rv.empty?) ? nil : rv
  end

  # get the name for an alias
  def get_name_by_alias alias_
    rv = @service.call('pastes.getNameByAlias', alias_)
    (rv.empty?) ? nil : rv
  end

  # return the paste "uid"
  def get_paste uid
    rv = @service.call('pastes.getPaste', uid)
    if not rv
      return nil
    end
    LodgeIt::Paste.new(self, rv)
  end

  # return the last "n" pastes
  def get_recent_pastes n
    @service.call('pastes.getRecent', n).map do |data|
      LodgeIt::Paste.new(self, data)
    end
  end

  # return the most recent paste
  def get_recent_paste
    self.get_recent_pastes(1).first
  end

  # return all pastes for a given tag name
  def get_pastes_for_tag tag
    @service.call('pastes.getPastesForTag', tag).map do |data|
      LodgeIt::Paste.new(self, data)
    end
  end

  # return the url or a paste
  def get_paste_url uid
    rv = @service.call('pastes.getURL', uid)
    (rv.empty?) ? nil : rv
  end

  # create a new paste
  def new_paste code, language='text', private_=false, title='Untitled',
                author='anonymous', tags=[]
    if language != 'text' and not self.language_exists(language)
      raise AttributeError, "unknown language '#{language}'"
    end
    rv = @service.call('pastes.newPaste', language, code, private_,
                       title, author, tags)
    if rv == 0
      return nil
    end
    Paste.new(self, rv['uid'])
  end

  # check if a file exists
  def style_exists? style
    @service.call('styles.styleExists', style.to_s)
  end

  # return a list of supported styles
  def get_style_list
    @service.call('styles.getStyleList').map { |x| x.to_sym }
  end

  # return the css file of a name or nil if the style does
  # not exist. If prefix is given, all css definitions will
  # be prefixed with it (eg: "div.syntax")
  def get_style style, prefix=''
    rv = @service.call('styles.getStyle', style, prefix)
    (rv.empty?) ? nil : rv
  end

  # return a tag cloud. The return values is a hash with
  # the following keys:
  #
  #   name      name of the tag
  #   size      size of the tag in pixels
  #   count     number of pastes tagged with this tag
  def get_tag_cloud
    @service.call('tags.getTagCloud')
  end


  # == Paste
  #
  # This class represents a paste. You should not create instances
  # of this class yourself.
  class Paste

    attr_reader(:uid, :title, :author, :private, :pub_date,
                :code, :parsed_code, :language, :language_name,
                :url, :tags)
    
    def initialize agent, data
      @agent = agent
      @uid = data['uid']
      @title = data['title']
      @author = data['author']
      @private = data['private'] || false
      @pub_date = Time.at(data['pub_date'])
      @code = data['code']
      @parsed_code = data['parsed_code']
      @language = data['language']
      @language_name = data['language_name']
      @url = data['url']
      @tags = data['tags']
      @reply_to = (data['reply_to'].empty?) ? nil : data['reply_to']
      
      # used as cache for reply_to
      @_reply_to = nil
    end

    def inspect
      "#<LodgeIt::Paste '#{@uid}'>"
    end

    def reply_to
      if not @reply_to.nil?
        if not @_reply_to
          @_reply_to = @agent.get_paste(@reply_to)
        end
        return @_reply_to
      end
      nil
    end

  end

end
